import sublime
import sublime_plugin

import subprocess
import os
import shutil
import socket
import threading
import time

from .xml_reader import xml_to_bibl


line_nummer = 0
lines_bibl = {}
addr_bibl = {}
peripheral = {}
menu_item = ""
debug_focus = None
openocd_process = None
start = 0
SOCKET = None

##################
class DebugOpenocdCommand(sublime_plugin.TextCommand): 		# отладка проекта
	def run(self, edit):
		global terminal
		global start
		global peripheral
		global debug_focus

		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]
		if syntax == "Assembler_GNU":

			path = self.view.file_name()

			sublime.run_command("new_window")
			window = sublime.active_window()

			terminal = sublime.active_window().create_output_panel('info_panel')
			terminal.assign_syntax("Assembler_GNU.sublime-syntax")
											
			window.set_layout({
				"cols": [0.0, 0.3, 0.7, 1.0],
				"rows": [0.0, 1.0],
				"cells": [[0, 0, 1, 1], [1, 0, 2, 1], [2, 0, 3, 1],]
				})

			
			###########
			view_register = window.new_file()
			view_register.set_name(f"Registers")
			view_register.set_scratch(True)
			view_register.settings().set("font_size", 11)		
			view_register.settings().set("gutter", False)
			view_register.assign_syntax("Assembler_GNU.sublime-syntax")
			window.set_view_index(view_register, 2, 0)

			###########
			view_periph = window.new_file()
			view_periph.set_name(f"Peripheral")
			view_periph.set_scratch(True)
			view_periph.settings().set("font_size", 11)		
			view_periph.settings().set("gutter", False)
			view_periph.assign_syntax("Assembler_GNU.sublime-syntax")
			window.set_view_index(view_periph, 0, 0)
			
			###########
			file_path = path.split("\\")[:-1]
			name = file_path[-1]
			path = ""
			for i in file_path:
				path += i + "\\"

			###########
			folder_list = os.listdir(path)
			for file in folder_list:
				if ".asm" in file or ".ASM" in file or ".s" in file or ".S" in file:
					if "main" in file:
						index = 0
					else:
						index = 1

					filename = path + file

					view_main = window.open_file(filename)
					view_main.set_scratch(True)
					view_main.settings().set("font_size", 10)
					view_main.set_read_only(True)
					window.set_view_index(view_main, 1, index)
					if index == 0:
						debug_focus = view_main


			############
			path_dbg = path + "dbg\\lines.dbg"
			lines_to_bibl(path_dbg)

			path_sasm = path + "dbg\\project.sasm"
			addr_to_bibl(path_sasm, name)

			path_inc = path + "inc"
			folder_list = os.listdir(path_inc)
			xml = ""
			for file in folder_list:
				if ".xml" in file or ".XML" in file:
					xml = file
					break

			if xml != "":
				path_xml = path + f"inc\\{xml}"
				peripheral = xml_to_bibl(path_xml)			

				sublime.set_timeout(lambda: sublime.active_window().run_command("update_peripheral"), 0)
			else:			
				text = "\n >> Please place the file with\n   peripherals in </inc> folder..."
				view_periph.run_command("insert", {"characters": text})

			window.run_command("openocd_start")
				

##################
class UpdateRegistersCommand(sublime_plugin.WindowCommand):
	def run(self, text):
		
		target_view = None
		for view in self.window.views():
			if view.name() == "Registers":
				target_view = view
				break

		if target_view == None:
			window = sublime.active_window()
			target_view = window.new_file()
			target_view.set_name(f"Registers")
			target_view.set_scratch(True)
			target_view.settings().set("gutter", False)
			view_register.assign_syntax("Assembler_GNU.sublime-syntax")
			window.set_view_index(target_view, 2, 0)
		
		
		target_view.run_command("edit_registers", {"text": text})

		
##################
class EditRegistersCommand(sublime_plugin.TextCommand):
	def run(self, edit, text):			
		region = sublime.Region(0, self.view.size())
		self.view.replace(edit, region, text)
		self.view.sel().clear()


##################
class DebugLineCommand(sublime_plugin.TextCommand):
	def run(self, edit, filename, next_line):
		global line_nummer

		self.view.set_read_only(False)
		line_position = self.view.text_point(line_nummer, 0)
		line_position = self.view.line(line_position)
		line_text = self.view.substr(line_position)
		line_text = line_text.replace(":>", "")
		self.view.replace(edit, line_position, text=line_text)
		self.view.set_read_only(True)
		
		sublime.active_window().run_command("debug_linea", {"filename": filename, "next_line": next_line})

##################
class DebugLineaCommand(sublime_plugin.WindowCommand):
	def run(self, filename, next_line):
		global line_nummer
		global debug_focus

		target_view = None
		for view in self.window.views():
			if view.file_name() == filename:
				target_view = view
				debug_focus = target_view
				break

		# если нужный файл еще не открыт -> открываем его
		window = sublime.active_window()
		if target_view == None:
			if "main" in filename:
					index = 0
			else:
				index = 1
			target_view = window.open_file(filename)
			target_view.set_scratch(True)
			target_view.settings().set("font_size", 10)
			window.set_view_index(target_view, 1, index)
		
		window.focus_view(target_view)
		target_view.run_command("debug_lineb", {"next_line": next_line})

##################
class DebugLinebCommand(sublime_plugin.TextCommand):
	def run(self, edit, next_line):
		global line_nummer

		self.view.set_read_only(False)
		line_position = self.view.text_point(next_line, 0)
		line_position = self.view.line(line_position)
		self.view.insert(edit, line_position.a, text=":>")
		self.view.show(line_position.a)
		line_nummer = next_line
		self.view.set_read_only(True)


##################
def lines_to_bibl(path):
	global lines_bibl

	with open (path, 'r', encoding='utf-8') as file:
		while(1):
			line = file.readline().replace("\n", "")
			if len(line) < 2:
				break

			if ":" in line:
				spisok = file.readline().replace("\n", "").replace(" ", "")
				spisok = spisok.split(",")
				lines_bibl[line] = spisok

##################
def addr_to_bibl(path, name):
	global addr_bibl
	global lines_bibl

	clock = 0
	with open (path, 'r', encoding='utf-8') as file:
		while(1):
			line = file.readline().replace("\n", "")
			if len(line) < 2:
				clock += 1
			else:
				clock = 0
			if clock > 5:
				break

			if name in line:
				line = line.split(":")
				bibl_name = line[1].split("/")[-1]
				bibl_name = bibl_name.replace(".", "_") + ":"

				file_name = line[0] + ":" + line[1].replace("/", "\\").replace("\\tmp", "")
				line_nummer = line[2]
				try:
					line_nummer = lines_bibl[bibl_name][int(line_nummer)]
				except:
					None

				line_addr = file.readline()
				if ".word" not in line_addr and ".short" not in line_addr and ".byte" not in line_addr:
					addr = line_addr.split(":")[0].replace(" ", "")
					addr = f"{addr:0>8}"
					
					if addr != "\n" and addr != "0000000\n":
						addr_bibl[addr] = [file_name, line_nummer]
	
################
class OpenocdSendCommand(sublime_plugin.WindowCommand):
	def run(self, command):
		global debug_focus

		sublime.active_window().focus_view(debug_focus)
		print(debug_focus.file_name())
		self.command = command
		# Запускаем поток, чтобы не блокировать UI редактора
		thread = threading.Thread(target=self.network_task, args=(command,))
		thread.start()
		
		
	#################
	def network_task(self, command):
		global SOCKET

		SOCKET = get_socket()
		if SOCKET:
			try:
				if command != "next":
					SOCKET.sendall(f"{command}".encode('utf-8') + b'\x1a')

				create_terminal("")
				print_terminal(f'>> OpenOCD: "{command}"')				

				SOCKET.sendall(f"targets".encode('utf-8') + b'\x1a')
				time.sleep(0.2)
				self.read_answer()
				
			except Exception as e:
				self.on_error(str(e))

	################
	def read_answer(self):
		response = SOCKET.recv(256).decode('utf-8').replace('\x1a', '').strip()
		if "halted" in response:			
			SOCKET.sendall(f"reg".encode('utf-8') + b'\x1a')
			time.sleep(0.2)
			self.registers_read(1)
			self.filename = addr_bibl[self.pc][0]
			self.next_line = int(addr_bibl[self.pc][1])

			if self.command == "next":
				self.next_command()
				time.sleep(0.21)

			sublime.active_window().run_command("debug_line", {"filename": self.filename, "next_line": (self.next_line - 1)})

		else:
			sublime.set_timeout(lambda: self.registers_read(0), 100)
		print_terminal(">> ")
		sublime.active_window().run_command("update_peripheral", {"current_menu": menu_item})

	##############
	def registers_read(self, halt):
		if halt == 1:
			spisok = SOCKET.recv(1280).decode('utf-8').replace('\x1a', '').strip()
			spisok = spisok.split("\n")
			spisok = spisok[1:-1]

			registers = ""

			for i in range(len(spisok)):
				spisok[i] = spisok[i].split(" ")
				try:
					if spisok[i][1].upper() == "PC":
						self.pc = spisok[i][3].replace("0x", "")

					if i <= 12 or i >= 23:
						spisok[i] = f"{spisok[i][1].upper():<9} : {spisok[i][3]:>10} :: {int(spisok[i][3], 16)}"
					else:
						spisok[i] = f"{spisok[i][1].upper():<9} : {spisok[i][3]:>10} :: "
					registers += spisok[i] + "\n"

				except:
					None
		else: registers = ">> Waiting halt mode..."
		
		sublime.active_window().run_command("update_registers", {"text": registers})

	#############
	def next_command(self):		
		n = 0
		current_line = self.next_line
		while(1):
			n += 1
			self.next_line += 1
			target = [addr_bibl[self.pc][0], str(self.next_line)]
			next_addr = next((k for k, v in addr_bibl.items() if v == target), None)

			if next_addr != None:
				next_addr = int(next_addr,16) + 1
				next_addr = f"{next_addr:x}"

				next_command = f"bp 0x{next_addr} 2 hw; resume; wait_halt; rbp 0x{next_addr}"						
				SOCKET.sendall(f"{next_command}".encode('utf-8') + b'\x1a')
				time.sleep(0.1)

				SOCKET.sendall(f"reg".encode('utf-8') + b'\x1a')
				sublime.set_timeout(lambda: self.registers_read(1), 200)								
				break

			elif n == 10: # если следующая инструкция не найдена в следующих 10 строках -> делаем "step"
				self.next_line = current_line
				break
								
		
	def get_pc(self):		
		response = SOCKET.recv(256).decode('utf-8').replace('\x1a', '').strip()
		print_terminal(response)

	def on_error(self, e):
		sublime.error_message(f">> SOCKET: {e}")

################
class OpenocdSendReadCommand(sublime_plugin.WindowCommand):
	def run(self, command):
		thread = threading.Thread(target=self.network_task, args=(command,))
		thread.start()

	def network_task(self, command):
		global SOCKET
		global debug_focus

		sublime.active_window().focus_view(debug_focus)
		
		SOCKET = get_socket()
		if SOCKET:		
			try:			
				SOCKET.sendall(command.encode('utf-8') + b'\x1a')
				time.sleep(0.2)
				answer = SOCKET.recv(2560).decode('utf-8').replace('\x1a', '').strip()
				create_terminal("")
				print_terminal(f'>> OpenOCD: "{command}"')
				print_terminal(">> ")
				print_terminal("")
				print_terminal(answer)
					
			except Exception as e:
				sublime.error_message(f">> SOCKET: {e}")
		

################
class OpenocdStartCommand(sublime_plugin.WindowCommand):
	def run(self):
		global openocd_process
		global start

		if openocd_process and openocd_process.poll() is None:
			create_terminal("")
			print_terminal(">> OpenOCD: Debug is already running!")
			start = 1
			return


		##################
		path = os.path.abspath(__file__)
		path = path.split("\\")[:-1]
		path_folder = ""
		path_openocd = ""
		for i in path:
			path_folder += i + "\\"

		path_openocd = path_folder + "Openocd\\" 
		path_bat = path_openocd + "debug.bat"
		
		cmd = []
		with open (path_bat, 'r', encoding='utf-8') as file:
			while(1):
				line = file.readline().replace("\n", "").replace("\\","/")
				if len(line) < 2:
					clock += 1
				else:
					clock = 0
				if clock > 5:
					break

				if "openocd" in line:
					if line [-1] != " ": line += " "
					line = line.replace("  ", " ").replace("  ", " ")

					cmd = line.split(" ")[:-1]
					for i in range(len(cmd)):
						if "bin" in cmd[i]:
							cmd[i] = path_openocd + cmd[i]
						elif "interface" in cmd[i]:
							cmd[i] = path_openocd + "scripts/" + cmd[i]
						elif "target" in cmd[i]:
							cmd[i] = path_openocd + "scripts/" + cmd[i]
						elif "scripts" in cmd[i]:
							cmd[i] = path_openocd + cmd[i]
					
						cmd[i] = cmd[i].replace("\\", "/")

					break
	
		try:
			# creationflags нужен, чтобы не вылетало лишнее окно консоли
			startupinfo = None
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			
			openocd_process = subprocess.Popen(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,
				startupinfo=startupinfo,
				universal_newlines=True
			)
			
			threading.Thread(target=self.read_output, args=(openocd_process,)).start()
					
			
		except Exception as e:
			sublime.error_message(f">> OpenOCD: {e}")

		

	############### обработка ошибок SOCKET
	def read_output(self, process):
		global terminal
		global start
		
		for line in iter(process.stdout.readline, ""):
						
			if "Error" in line:
				error_text = f'>> OpenOCD: "{line.split(":")[-1].strip()}"'
				if "no breakpoint" not in error_text and "(BP" not in error_text and "not find" not in error_text and "not available" not in error_text:
					sublime.set_timeout(lambda: print_terminal(error_text), 0)
					process.terminate()
					process.stdout.close()
					start = 0
					break
				else:
					if "(BP" not in error_text:
						create_terminal("")
						sublime.set_timeout(lambda: print_terminal(f'{error_text}'), 0)
						sublime.set_timeout(lambda: print_terminal(">> "), 100)
					start = 1

			elif "starting gdb" in line:
				sublime.set_timeout(lambda: create_terminal(""), 0)
				sublime.set_timeout(lambda: print_terminal(">> OpenOCD: Debug mode active..."), 0)
				sublime.set_timeout(lambda: get_socket(), 200)

				start = 1

################
class AddPanelButtonCommand(sublime_plugin.WindowCommand):
	def run(self):
		
		# Добавляем "кнопку" через Phantom
		html = """
		<body id="my-button" style="padding-left: 300px;">
			<style>
				.btn {
					background-color: #007acc;
					color: white;
					padding: 3px 10px;
					text-decoration: none;
					border-radius: 7px;
					}
				.sys {
					background-color: green;
					color: white;
					padding: 3px 10px;
					text-decoration: none;
					border-radius: 7px;
					}
				
			</style>

			<a class="btn" href="reset run">Reset</a>
			<a class="btn" href="reset halt">Reset Halt</a>
			<a class="btn" href="halt">Halt</a>
			<a class="btn" href="step">Step</a>
			<a class="btn" href="next">Next</a>
			<a class="btn" href="resume">Resume</a>
			&nbsp;&nbsp;&nbsp;&nbsp;
			<a class="sys" href="run">RUN</a>
			<a class="sys" href="stop">STOP</a>

		</body>
		"""
		
		# Создаем набор фантомов для панели
		self.phantom_set = sublime.PhantomSet(terminal, "buttons")
		self.phantom_set.update([sublime.Phantom(sublime.Region(0, 0), html, sublime.LAYOUT_INLINE,
			on_navigate=self.on_click)])
		print_terminal(">> ")
		

	def on_click(self, href):
		sublime.active_window().focus_view(debug_focus)
		if href == "stop":
			stop_openocd()

		elif href == "run":
			sublime.active_window().run_command("openocd_start")
			
		else:
			sublime.active_window().run_command("openocd_send", {"command": href})
		

################
def stop_openocd():
	global openocd_process
	global SOCKET
	
	if openocd_process and openocd_process.poll() is None:
		print(">> OpenOCD: Close server...")
		create_terminal("")
		print_terminal(">> OpenOCD: Close server...")
		openocd_process.terminate() # Мягкое завершение
		openocd_process = None
	close_socket()


################
def print_terminal(text): 				# Вывод текста в Output Panel
	global terminal
	terminal.run_command('append', {'characters': f"{text}\n"})
	sublime.active_window().run_command('show_panel', {'panel': 'output.info_panel'})

################
def create_terminal(text): 				# Создание новой и вывод текста в Output Panel
	global terminal
	terminal = sublime.active_window().create_output_panel('info_panel')
	terminal.run_command('append', {'characters': f"{text}\n"})
	sublime.active_window().run_command('show_panel', {'panel': 'output.info_panel'})

################ 	устанавливаем соединение с OpenOCD через socket
def get_socket():
	global SOCKET

	if SOCKET is None:
		try:
			# Создаем соединение
			SOCKET = socket.create_connection(("127.0.0.1", 6666), timeout=2)
			# Убираем таймаут, чтобы сокет не закрывался при ожидании ответа
			SOCKET.settimeout(None)
			print_terminal(">> SOCKET: Connection complete...")
			sublime.set_timeout(lambda: sublime.active_window().run_command("add_panel_button"), 100)


		except Exception as e:
			print(f">> SOCKET: Connection failed: {e}")
			print_terminal(f">> SOCKET: Connection failed: {e}")
	return SOCKET

################## 	закрываем соединение с OpenOCD через socket
def close_socket():
	global SOCKET
	global menu_item

	menu_item = ""

	if SOCKET:
		try:
			SOCKET.shutdown(socket.SHUT_RDWR)
			SOCKET.close()
			print(">> SOCKET: Connection closed...")
			print_terminal(">> SOCKET: Connection closed...")
		except:
			pass
		SOCKET = None

##################
class BreakpointCommand(sublime_plugin.TextCommand):	
	def run(self, edit):
		self.edit = edit
		if self.view.is_read_only():
			self.view.set_read_only(False)

			point = self.view.sel()[0].begin()		
			line = self.view.rowcol(point)[0] + 1
			path = self.view.file_name()
			target = [path, str(line)]
			
			self.addr = next((k for k, v in addr_bibl.items() if v == target), None)
			
			if self.addr:
				self.line_position = self.view.line(point)
				self.line_text = self.view.substr(self.line_position)

				items = ["Breakpoint Set", "Breakpoint Delete"]	# index	
				self.view.show_popup_menu(items, self.on_done)

		self.view.set_read_only(True)

	def on_done(self, index):
		global SOCKET

		if index == 0:	# установка breakpoint
			self.line_text = "&" + self.line_text
			self.line_text = self.line_text.replace("&&", "&")
			self.view.replace(self.edit, self.line_position, text=self.line_text)

			
			command = f"bp 0x{self.addr} 2 hw"
			SOCKET.sendall(f"{command}".encode('utf-8') + b'\x1a')
			time.sleep(0.2)
			spisok = SOCKET.recv(1280).decode('utf-8').replace('\x1a', '').strip()
			create_terminal("")			
			print_terminal(f'>> OpenOCD: "Breakpoint set"')
			print_terminal(">> ")

			'''
			command = f"bp"
			SOCKET.sendall(f"{command}".encode('utf-8') + b'\x1a')
			time.sleep(0.2)
			spisok = SOCKET.recv(1280).decode('utf-8').replace('\x1a', '').strip()
			print_terminal(f'>> OpenOCD: \n{spisok}')
			'''

		elif index == 1: # удаление breakpoint
			self.line_text = self.line_text.replace("&", "")
			self.view.replace(self.edit, self.line_position, text=self.line_text)
			
			try:				
				command = f"rbp 0x{self.addr}"
				SOCKET.sendall(f"{command}".encode('utf-8') + b'\x1a')
				time.sleep(0.2)
				spisok = SOCKET.recv(1280).decode('utf-8').replace('\x1a', '').strip()

				command = f"bp"
				SOCKET.sendall(f"{command}".encode('utf-8') + b'\x1a')
				time.sleep(0.2)
				
				spisok = SOCKET.recv(1280).decode('utf-8').replace('\x1a', '').strip()
				create_terminal("")
				if spisok == "":
					print_terminal(f'>> OpenOCD: "All breakpoints was deleted"')
				else:
					print_terminal(f'>> OpenOCD: "Breakpoint was deleted"')
				print_terminal(">> ")							

			except Exception as e:
				None

##################
##################
class UpdatePeripheralCommand(sublime_plugin.WindowCommand):
	def run(self, current_menu=""):
		
		target_view = None
		for view in self.window.views():
			if view.name() == "Peripheral":
				target_view = view
				break

		if target_view == None:
			window = sublime.active_window()
			target_view = window.new_file()
			target_view.set_name(f"Peripheral")
			target_view.set_scratch(True)
			target_view.settings().set("gutter", False)
			view_register.assign_syntax("Assembler_GNU.sublime-syntax")
			window.set_view_index(target_view, 0, 0)
		
		
		target_view.run_command("edit_peripheral", {"current_menu": current_menu})

		
##################
class EditPeripheralCommand(sublime_plugin.TextCommand):
	def run(self, edit, current_menu=""):
		global peripheral

		self.phantom_set = sublime.PhantomSet(self.view, "tree_menu")

		self.dynamic_list = list(peripheral.keys())
		self.dynamic_list.sort()

		self.dynamic_text = ""
		self.dynamic_view(current_menu)


	################
	def render_tree(self):
		
		html = f"""
		<body id="tree-menu" style="padding-left: 10px;">
			<style>
				.sysOpen {{
					background-color: #007acc;
					color: white;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;

					}}
				.sys {{
					background-color: green;
					color: white;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;
					}}

				.group {{
					background-color: navy;
					color: white;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;
					}}

				.reg {{
					background-color: orange;
					color: black;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;
					}}

				.field {{
					background-color: pink;
					color: black;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;
					}}
				.regOpen {{
					background-color: red;
					color: black;
					padding: 2px 15px;
					text-decoration: none;
					border-radius: 3px;
					line-height: 0.8;
					}}
				
			</style>

			{self.dynamic_text}


		</body>
		"""
		

		self.phantom_set.update([sublime.Phantom(sublime.Region(0, 0), html, sublime.LAYOUT_INLINE,
			on_navigate=self.dynamic_view)])	


	##################
	def dynamic_view(self, element=""):
		global menu_item

		dynymic_text = ""

		if element != "":
			name = element			
			
			for periph in self.dynamic_list:
				change = 0
				if periph == name: 					# если нажали кнопку с периферией					
					space =  "&nbsp;" * (20 - len(periph))
					dynymic_text += f'<br><a class="sysOpen" href=".{periph}">{periph}{space}</a>'
					change = 1
					
					if len(peripheral[periph]) > 1:
						for group in peripheral[periph]:
							space =  "&nbsp;" * (20 - len(group))
							dynymic_text += f'<br><a class="group" href=".{periph}.{group}">{group}{space}</a>'
					else:
						name = f".{periph}.{list(peripheral[periph].keys())[0]}"
						

				elif f".{periph}" == name: 			# закрываем вкладку с переферией
					space =  "&nbsp;" * (20 - len(periph))
					dynymic_text += f'<br><a class="sys" href="{periph}">{periph}{space}</a>'
					name = name.replace(".", "")
					change = 1
					menu_item = ""


				########### первое вложение меню ##########
				if f".{periph}" in name:
					menu = name.split(".")[1:]
					
					if change == 0:
						space =  "&nbsp;" * (20 - len(periph))
						dynymic_text += f'<br><a class="sysOpen" href=".{periph}">{periph}{space}</a>'

					for group in peripheral[periph]:
						if len(peripheral[periph]) > 1:
							space =  "&nbsp;" * (20 - len(group))
							dynymic_text += f'<br><a class="group" href=".{periph}.{group}">{group}{space}</a>'

						if menu[1] == group:
							change = 1
							for register in peripheral[periph][group]:
								if isinstance(peripheral[periph][group][register], dict):
									space =  "&nbsp;" * (19 - len(register))
									shift = ""
									color = "reg"
									try:
										if menu[2] == register:
											color = "regOpen"
											shift = "&nbsp;"
											space =  "&nbsp;" * (30 - len(register))
									except:
										None

									dynymic_text += f'<br>&nbsp;{shift}<a class="{color}" href=".{periph}.{group}.{register}">{register}{space}</a>'

									try:
										if menu[2] == register:
											menu_item = name
											adr = int(peripheral[periph][group]["baseaddress"], 16) + int(peripheral[periph][group][register]["addressoffset"], 16)
											value = read_memory(hex(adr)) # читаем значение по адресу
											value_bin = int(value, 16)
											value_bin = f"{value_bin:032b}"
											value_bin = value_bin[::-1] # инвертируем биты																					

											for item in peripheral[periph][group][register]:
												if isinstance(peripheral[periph][group][register][item], dict):
													bitoffset = int(peripheral[periph][group][register][item]["bitoffset"])
													bitwidth = int(peripheral[periph][group][register][item]["bitwidth"])
													bits = value_bin[bitoffset:(bitoffset+bitwidth)]
													space =  "&nbsp;" * (18 - len(item))
													
													if len(bits) > 8:
														bits = "D: " + str(int(bits,2))
													
													space_bits = "&nbsp;" * (8 - len(bits))
													dynymic_text += f'<br>&nbsp;&nbsp;<a class="field">{item}{space}</a>'
													dynymic_text += f'<a class="sysOpen">{bits}{space_bits}</a>'
									except:
										None
				if change == 0:
					space = "&nbsp;" * (20 - len(periph))
					dynymic_text += f'<br><a class="sys" href="{periph}">{periph}{space}</a>'


		######## первоначальный вид 
		else:
			for keys in self.dynamic_list:
				space =  "&nbsp;" * (20 - len(keys))
				dynymic_text += f'<br><a class="sys" href="{keys}">{keys}{space}</a>'
			

		self.dynamic_text = dynymic_text
		self.render_tree()
	


##################
def read_memory(adr):
	global SOCKET
	value = "---"

	SOCKET = get_socket()
	if SOCKET:
		command = f"mdw {adr}"
		SOCKET.sendall(command.encode('utf-8') + b'\x1a')
		time.sleep(0.12)
		
		try:
			value = SOCKET.recv(256).decode('utf-8').replace('\x1a', '').strip()
			value = value.split(":")[1]
		except:
			None

	return value

