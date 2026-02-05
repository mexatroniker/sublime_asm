import sublime
import sublime_plugin

import subprocess
import os
import shutil
from .include import include, import_include
from .Assembler_GNU import op_1, register
import time

timer = 0
asm_files = ("ASM", "S")
macros = {}
include_global = {}
flash = 0
terminal = sublime.active_window().create_output_panel('info_panel')
terminal.assign_syntax("Assembler_GNU.sublime-syntax")

###### преобразуем список OPER до 3 знаков
op_1 = list(op_1)
for i in range(len(op_1)):
	op_1[i] = op_1[i][:3]
op_1 = tuple(op_1)

#####################
class CompileAndFlash(sublime_plugin.TextCommand): 		# компиляция и прошивка проекта
	def run(self, edit):
		global flash
		flash = 1

		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]
		if syntax == "Assembler_GNU":
			self.view.run_command('compile_equ')
		
#####################
class CompileOnly(sublime_plugin.TextCommand): 		# компиляция проекта
	def run(self, edit):
		global flash
		flash = 0

		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]
		if syntax == "Assembler_GNU":
			self.view.run_command('compile_equ')

#####################
class CompileEquCommand(sublime_plugin.TextCommand):  # глобальные переменные для всего проекта
	def run(self, edit):
		global include
		global include_global
		global timer
		timer = time.time()

		include_global = {}

		###################
		views = sublime.active_window().views() 	# Список открытых файлов в Sublime Text

		for view in views:
			current_view = view.file_name() 			# получаем адрес открытого файла
			if current_view:
				print(current_view)
				current_view = current_view.split("\\")
				
				file_name = current_view[-1]
				
				try:
					file_name = file_name.split(".")[-1].upper()
				except:
					file_name = "None"

				if file_name in asm_files: 					# если файл имеет расширение из <asm_files>
					view.run_command('save')				# сохраняем все открытые файлы
		###########

		path = self.view.file_name() 				# текущее положение файла <.asm>

		path = path.split("\\")
		folder = path[:-1]
		bibl = folder[-1] 							# имя библиотеки
		path = ""
		for i in folder:
			path += i + "\\"
													# в path адрес папки проекта
		file_list = os.listdir(path)				# получаем список файлов в папке проекта
		filter_list = []

		for i in file_list:
			try:
				if i.split(".")[1].upper() in asm_files:
					filter_list.append(i)
			except:
				None
		
		for name in filter_list:
			filename = f"{path}\\{name}"

			with open (filename, 'r', encoding='utf-8') as file:
				clock = 0
				while(1):
					line = file.readline()
					if (len(line)) == 0:
						clock += 1
						if clock == 10: break
					else:
						clock = 0

					# обработка <.EQU>
					if ".equ" in line or ".EQU" in line:
						line = line.replace(",", "").replace("\n", "").split("@")
						if len(line) == 1:
							line.append("")

						comment = f"from <{name}>   {line[1]}"
						line = line[0].split(" ")[1:]

						try:
							try:
								include_global[line[0]] = [int(line[1]), f"{hex(int(line[1]))}", comment]
							except:
								include_global[line[0]] = [int(line[1], 16), f"{line[1]}", comment]
						except:
							include_global[line[0]] = [">>", f"{line[1]}", comment]


					# обработка <.GLOBAL>
					elif ".global" in line or ".GLOBAL" in line:
						line = line.split(" ")
						line[1] = line[1].replace("\n", "")						
						include_global[f"{line[0]} {line[1]}"] = ["", f"{line[1]}",  f"<label> from <{name}>"]

					# обработка <.MACRO>
					elif ".macro" in line or ".MACRO" in line:
						line = line.split(" ")
						line[1] = line[1].replace("\n", "")						
						include_global[f"{line[0]} {line[1]}"] = ["", f"{line[1]}",  f"<macros> from <{name}>"]

		bibl_global = bibl + "_global"
		include[bibl_global] = include_global

		self.view.run_command('compile_files')
				


################
class CompileFilesCommand(sublime_plugin.TextCommand): 
	
	def run(self, edit):
		head_end = 0
		after_head = 0
		head = []
		error = 0
		global flash
		global macros
		global terminal
		global include
		global timer
		
		
		###########

		path = self.view.file_name() 					# текущее положение файла <.asm>
		path = path.split("\\")[:-1] 					# адрес папки проекта

		bibl_name = path[-1] 							# имя бибилиотеки
		bibl_global = bibl_name + "_global"
		bibl_set = bibl_name + "_set"
		
		################
		if bibl_name not in include: 					# если библиотека include отстутствует
			
			current_view = self.view.file_name() 			# получаем адрес открытого файла
			current_view = current_view.split("\\")
			
			file_name = current_view[-1]
			
			try:
				file_name = file_name.split(".")[-1].upper()
			except:
				file_name = "None"

			current_path = ""
			if file_name in asm_files: 					# если файл имеет расширение из <asm_files>
				current_view = current_view[:-1]
				
				for i in current_view:
					current_path += i + "\\"
			
			path = [current_path]
			bibl_name = current_path.split("\\")[-2]			# имя папки проекта = имя библиотеки {include}
							
			exec(f"{bibl_name} = {{}}", globals())			# создаем библиотеку для include
			include[bibl_name] = eval(bibl_name)			# помещаем новую библиотеку в include
			
			for item in path:
				folder_list = os.listdir(item)
				
				for i in folder_list:
					if i == "inc" or i == "INC":
						path.append(item + i) 				# если есть папка <\inc>, добавляем ее в список путей <path>
				
				filename = ""
				for i in folder_list:
					if ".inc" in i or ".INC" in i:
						filename = i
						path_file = item + "\\" + filename
						
						import_include(path_file, eval(bibl_name)) 			# импортируем <include> из файла <.inc>
		

		############
		terminal = sublime.active_window().create_output_panel('info_panel')
		bibliothek = {**include[bibl_name], **include[bibl_global]}

				
		folder = ""
		for i in path:
			folder += i + "\\"

		temp_file_list = os.listdir(folder) 			# создаем папку tmp если ее нет
		if "tmp" not in temp_file_list:
			os.mkdir(folder + "tmp")

		if "bin" not in temp_file_list:					# создаем папку bin
			os.mkdir(folder + "bin")

		tmp_path = folder + "tmp"
		folder_tmp = os.listdir(tmp_path)

		for i in folder_tmp:
			os.remove(f"{tmp_path}\\{i}") 				# очищаем папку tmp


		file_list = []
		for file in temp_file_list:
			if ".ASM" in file.upper() or ".S" in file.upper():
				file_list.append(file)


		################### считываем каждый файл проекта в список <file_asm>

		for name in file_list:
			filename = f"{folder}{name}"
			list_name = name.replace(".", "_")
			temp_list = []
		
			with open (filename, 'r', encoding='utf-8') as file:
				clock = 0
				head_flag = 0
				number = 0
				set_list = []
				label_list = []

				while(1):
					skip = 0
					number += 1
					line = file.readline()
					check_line = line.replace("\t", "").replace(" ", "")
					check_line = len(check_line)
					
					if check_line <= 1:
						clock += 1
						if clock == 10: break
					else:
						clock = 0
					##############

					if "<head>" in line:
						head_flag = 1
					if "</head>" in line or "<\\head>" in line:
						head_flag = 2

					##############
					if clock < 3: 					# если пустых строк не больше 2
						if head_flag == 1:
							head.append(line) 		# если начался заголовок main
							head_end += 1
						elif head_flag == 2:
							head.append("@ ------------")
							head.append("\n")
							head = head[1:]
							head_flag = 3
							head_end += 3
							after_head = head_end
						elif head_flag == 3:
							temp_list.append(["\t\n", number])
							temp_list.append(["@ ------------\n", number])
							temp_list.append(["@ ------------\n", number])
							temp_list.append(["\t\n", number])
							head_flag = 0
							
						######################
						# обрабатываем строку со скобками
						if "(" in line and ")" not in line:

							temp_line = line
							while(1):
								number += 1
								line = file.readline().replace("\t", "")
								i = 0
								for i in range(len(line)):
									if line[i] != " ":
										break
								line = line[i:]

								if ")" in line:
									temp_line += line
									break
								else:
									temp_line += line

							line = temp_line.replace("\n", "")
							line += "\n"

						elif ".MACRO" in line or ".macro" in line:
							skip = 1
							macro_name = line.split(" ")[1]
							macros[macro_name] = []

							temp_list.insert(after_head, ["\n", number])
							after_head += 1
							while(1):
								macros[macro_name].append(line)
								temp_list.insert(after_head, [line, number])
								after_head += 1
								line = file.readline()
								number += 1
								if ".ENDM" in line or ".endm" in line:
									temp_list.insert(after_head, [line, number])
									macros[macro_name].append(line)
									line = ""
									break


						elif ".SET" in line or ".set" in line:
							set_temp = line.split(" ")
							set_list.append(set_temp[1].replace(",", ""))
							# добавили .set в список set_list
							skip = 1
							temp_list.insert(head_end, [line, number])
							head_end += 1
							after_head = head_end
							
							line = ""

						# обработка label	
						elif len(line) > 0:
							if line[0] != "\t" and line[0] != "." and ":" in line:
								label_temp = line.split(":")
								if len(label_temp) > 0:
									label_list.append(label_temp[0])

						elif ".EQU" in line or ".equ" in line:
							skip = 1

						######################
						if skip == 0:
							temp_list.append([line, number])

			# проходимся по файлу <main.asm>
			current_file = f"{list_name}_number"
			exec(f"{current_file} = []", globals())

			spisok = []
			for i in temp_list:
				spisok.append(i[0])
				eval(current_file).append(i[1])
			
			for i in range(len(spisok)):
				spisok[i] = spisok[i].replace("#", "@").replace(";", "@").replace("=", "= ")
				
				spisok[i] = spisok[i].split("@")
				if len(spisok[i]) > 1:
					temp_comment = "@" + spisok[i][1].replace("\n", "")

					only_comment = len(spisok[i][0])
					if len(spisok[i][0].replace("\t", "")) == 0:
						spisok[i][0] = ("\t" * only_comment) + temp_comment + "\n"
						temp_comment = ""
						
				else:
					temp_comment = ""
										

				spisok[i] = spisok[i][0]
				temp = spisok[i]

				if len(temp) > 1:
					if "@" not in temp and "global" not in temp and "GLOBAL" not in temp:

						spisok[i] = spisok[i].replace("\t", "$").replace("\n", "").replace("(", "( ").replace(")", " ) ").replace(">>", " >> ").replace("<<", " << ").replace("|", " | ").replace("+", " + ").replace("  ", " ")
						spisok[i] = spisok[i].split(" ")
						# spisok[i] -> строка в списке файла

						k = 0
						oper = ""
						len_spisok = len(spisok[i])

						macros_op = spisok[i][0].replace("$", "")
						if "(" in macros_op:
							macros_op = macros_op.replace("(", "")
							if macros_op not in macros:
								error += 1
								print_terminal(f'>> Attention: File <{name}> <line {temp_list[i][1]}> : <macros> "{macros_op}" not found...')

						for k in range(len_spisok): 		# определяем индекс OPER -> k
							item = spisok[i][k].replace("$", "")[0:3]
							if item in op_1 or "B" in item:
								oper = item
								break
						
						len_oper = len(spisok[i][k].replace("$", ""))
						if len_oper > 3: len_oper -= 1
						
						if oper in op_1 or "B" in oper:

							spisok[i][k] += " " * (6 - len_oper)
							
							temp = "" 			# сохраняем первую часть строки с OPER
							for s in range(k+1):
								char = spisok[i][s]
								if char == "":
									char = "  "
								if ":" in char:
									char += " "
								temp += char

							temp_spisok = spisok[i][k:]

							for n in range(1, len(temp_spisok)):
								if spisok[i][n+k] == "":
									spisok[i][n+k] = " "
								# функция замены include в строке
								else:
									if spisok[i][n+k][0].isalpha() and spisok[i][n+k].replace(",", "") not in register:
										try:
											spisok[i][n+k] = bibliothek[spisok[i][n+k]][1]
											# простая проверка есть ли значение в библиотеке

										except:									
											try:
												global_label = f".GLOBAL {spisok[i][n+k]}"
												spisok[i][n+k] = bibliothek[global_label][1]										
											except:
												try:
													global_label = f".global {spisok[i][n+k]}"
													spisok[i][n+k] = bibliothek[global_label][1]
												except:
													if spisok[i][n+k] not in set_list and spisok[i][n+k] not in label_list:
														error += 1
														print_terminal(f'>> Attention: File <{name}> <line {temp_list[i][1]}> : "{spisok[i][n+k]}" not found...')
														
											
								temp += spisok[i][n+k]

							temp += temp_comment + "\n"
							temp = temp.replace("$", "\t").replace(",", ", ")
						
						#if temp[0] == ".":
							#temp = temp.replace("\n","") + temp_comment + "\n"	
					temp = temp.replace("\n","") + temp_comment + "\n"
				spisok[i] = temp
						

			####################
			exec(f"{list_name} = {spisok}", globals())
			####################

		if error == 0: 					# компилируем проект
			#print_terminal(">> Compile  successfully complete...")
			print_terminal("------------")

			################ записываем новые скомпилированные файлы в \tmp
			for name in file_list:
				filename = f"{folder}tmp\\{name}"
				list_name = name.replace(".", "_")
				current_file = eval(list_name)
						
				with open (filename, 'w', encoding='utf-8') as file:
					if list_name != "main_asm":
						for i in head:
							file.write(i)

					for i in current_file:
						file.write(i)

			################
			path = os.path.abspath(__file__)
			path = path.split("\\")[:-1]
			path_compiler = ""
			path_openocd = ""
			for i in path:
				path_compiler += i + "\\"

			path_openocd = path_compiler + "Openocd\\"
			path_compiler += "Compiler\\"
			
			path_bat = path_compiler + "compiler.bat"
			path_link_bat = path_compiler + "linker.bat"
			path_obj_bat = path_compiler + "object.bat"
			path_size_bat = path_compiler + "size.bat"

			text_bat = []

			for name in file_list:
				output_name = name.split(".")[0]
				output_name += ".o"

				filename = f"{folder}tmp\\{name}"
				output_name = f"{folder}tmp\\{output_name}"

				text_bat.append(f'arm-none-eabi-as.exe -o "{output_name}" "{filename}"\n\n')


			# создаем compiler.bat для компиляции проекта
			with open (path_bat, 'w', encoding='utf-8') as file:
				file.write("echo off\ncls\n\n")
				for i in text_bat:
					file.write(i)
									
			
			result = subprocess.Popen(["compiler.bat"], cwd=path_compiler, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			stdout, stderr = result.communicate()

			process = stderr.split("\n")[:-1]
			if len(process) != 0:
				
				print_terminal(">> Compile  successfully complete...")
				print_terminal("-------------")
				for i in range(len(process)):
					
					process[i] = process[i].split("\\")[-1].replace(":", " : ").replace("'", "").replace("  ", " ")
					current_file = f"{process[i].split(':')[0].replace('.', '_').replace(' ', '')}_number"
					item = process[i].split(":")
					for n in range(len(item)):
						try: # меняем номер строки на номер в исходном файле
							temp = item[n].replace(" ", "")
							item[n] = int(temp)

							if "main" not in current_file:
								item[n] -= len(head) - 1

							item[n] = eval(current_file)[item[n]] - 1
							item[n] = f" {item[n]} "
						except:
							None

					process[i] = ""
					item = [x for x in item if x != " "]
					for m in item:
						process[i] += str(m) + ":"
					process[i] = process[i][:-1]

				text = ">> Attention:"
				process.insert(0, text)
				for i in process:
					if "Assembler messages" in i:
						print_terminal("-------------")
					else:
						print_terminal(i)

				print_terminal("-------------")
				error = 1
			else:
				#print_terminal(">> Assembly successfully complete...")
				#print_terminal("------------------------")
				error = 0

		################### начинаем линковку проекта
		if error == 0:
			
			input_name = ""
			ld_name = ""
			elf_name = ""
			for name in temp_file_list:
				try:
					name = name.split(".")
					if name[1] == "asm":
						input_name += (f'"{folder}tmp\\{name[0]}.o" ')
						elf_name = f"{folder}tmp\\project.elf"
					elif name[1] == "ld":
						ld_name = f"{folder}{name[0]}.ld"
				except:
					None

			if ld_name == "":
				print_terminal(f">> Attention: Link file <example.ld> not found...")
				print_terminal("------------------------")
				error = 1


			else:				
				text_bat = f'arm-none-eabi-ld.exe -T "{ld_name}" -o "{elf_name}" {input_name}\n'

				# создаем linker.bat для линковки проекта
				with open (path_link_bat, 'w', encoding='utf-8') as file:
					file.write("echo off\ncls\n\n")
					file.write(text_bat)

				result = subprocess.Popen(["linker.bat"], cwd=path_compiler, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
				stdout, stderr = result.communicate()

				process = stderr.split("\n")[:-1]

				if len(process) != 0:
					print_terminal(">> Assembly successfully complete...")
					print_terminal("------------------------")
					for i in range(len(process)):
						process[i] = process[i].split("\\")[-1].replace(":", " : ").replace("'", "").replace("  ", " ")
						current_file = f"{process[i].split(':')[0].replace('.', '_').replace(' ', '')}_number"
						item = process[i].split(":")
						
					process[i] = ""
					item = [x for x in item if x != " "]
					for m in item:
						process[i] += str(m) + ":"
					process[i] = process[i][:-1]

					text = ">> Attention:"
					process.insert(0, text)
					for i in process:
						print_terminal(i)

					print_terminal("-------------")
					error = 1

				else:
					#print_terminal(f">> Linker  successfully  complete...")
					#print_terminal(f"------------------------------------")
					error = 0

		################# создаем файлы .bin .hex
		if error == 0:
			text_bat = f'arm-none-eabi-objcopy.exe -O binary "{folder}tmp\\project.elf" "{folder}bin\\project.bin" \n'
			text_bat += f'arm-none-eabi-objcopy.exe -O ihex "{folder}tmp\\project.elf" "{folder}bin\\project.hex" \n'

			# создаем object.bat для линковки проекта
			with open (path_obj_bat, 'w', encoding='utf-8') as file:
				file.write("echo off\ncls\n\n")
				file.write(text_bat)


			result = subprocess.Popen(["object.bat"], cwd=path_compiler, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
			stdout, stderr = result.communicate()

			process = stderr.split("\n")[:-1]

			if len(process) != 0:
				print_terminal(f">> Linker  successfully  complete...")
				print_terminal(f"------------------------------------")
				for i in range(len(process)):
					process[i] = process[i].split("\\")[-1].replace(":", " : ").replace("'", "").replace("  ", " ")
					current_file = f"{process[i].split(':')[0].replace('.', '_').replace(' ', '')}_number"
					item = process[i].split(":")
					
				process[i] = ""
				item = [x for x in item if x != " "]
				for m in item:
					process[i] += str(m) + ":"
				process[i] = process[i][:-1]

				text = ">> Attention:"
				process.insert(0, text)
				for i in process:
					print_terminal(i)

				print_terminal("-------------")
				error = 1

			else:
				timer = int((time.time() - timer) * 1000)
				print_terminal(f">> Firmware file successfully created : {timer} ms")
				print_terminal(f"----------------------------------------------------------------")

				text_bat = f'arm-none-eabi-size.exe -t  "{folder}tmp\\project.elf"'
				with open (path_size_bat, 'w', encoding='utf-8') as file:
					file.write("echo off\ncls\n\n")
					file.write(text_bat)


				result = subprocess.Popen(["size.bat"], cwd=path_compiler, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
				stdout, stderr = result.communicate()

				process = stdout.split("\n")[2:-2]
				process[0] = process[0][1:]

				for stroka in process:
					stroka = stroka.split("\t")
					filename = stroka[-1]
					stroka = stroka[0:3]
					stroka.append(f'"{filename}"')
					stroka[-1] = stroka[-1].replace('"filename"', '<filename>')

										
					stroka[-1] = "    |   " + stroka[-1]
					temp = ""
					for i in stroka:
						temp += str(i)
					
					print_terminal(temp)
				print_terminal("----------------------------------------------------------------")
				error = 0
				################# файл прошивки успешно создан ############

				if flash == 1:
					openocd = f"{folder}openocd.bat"
									
					try:
						spisok = []					
						with open(openocd, 'r', encoding='utf-8') as file:
							clock = 0
							while(1):
								line = file.readline().replace("\t", "").replace("\n", "")
								leng = len(line)
								if leng > 0 and line[0] == "-":
									spisok.append(line)
									clock = 0
									
								else:
									clock += 1
									if clock > 5: break

						temp = ""
						interface = ""
						for line in spisok:
							if "interface" in line:
								interface = line.split("/")[1].replace(".cfg", "")
							elif "<bin/project.bin>" in line:
								folder = folder.replace("\\", "/")
								line = line.replace("<bin/project.bin>", f'"{folder}bin/project.bin"')
							temp += line + " "

						text_bat = f'bin\\openocd.exe {temp}'

						filename = path_openocd + "openocd.bat"
						with open (filename, 'w', encoding='utf-8') as file:
							file.write("echo off\ncls\n\n")
							file.write(text_bat)

						#print_terminal(">> Start MCU flash...")

						result = subprocess.Popen(["openocd.bat"], cwd=path_openocd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
						stdout, stderr = result.communicate()

						text = stderr.split("\n")
						text_error = [">> Openocd:", "-------------------------"]
						text_ok = [">> Openocd:", "-------------------------"]

						for item in text:
							if "rror" in item:
								if "open"in item:
									item = ">> " + item + f" interface <{interface}>..."
								text_error.append(item)
							elif "**" in item:
								item = item.replace("**", ">>")[:-2]
								text_ok.append(item)

						if len(text_error) > 2:
							text = text_error
						else:
							text = text_ok
						

						for i in text:
							print_terminal(i)



					except FileNotFoundError:
						print_terminal("Attention: >> File <openocd.bat> not found...")

					except OSError:
						print_terminal("Attention: >> Directory <Packages\\Openocd> not found...")


					flash = 0


################
class ShowTerminalPanelCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		sublime.active_window().run_command('show_panel', {'panel': 'output.info_panel'})

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
################			
