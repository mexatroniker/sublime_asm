import sublime
import sublime_plugin
import os
import shutil

from .include import include, import_include

#path = os.path.abspath(__file__)
#path_directory = os.path.dirname(path) + "\\include"
#print(f">> {path_directory}")


print(f">> Python 3.8 active!")

# список переменных
register = ('R0','R1','R2','R3','R4','R5','R6','R7','R8','R9','R10','R11','R12','LR','SP','PC','IP')
oper = ('SEL', 'CBZ', 'CBNZ', 'TBB', 'TBH', 'BKPT', 'CPSIE', 'CPSID')
oper_cond = ('CLREX', 'PUSH', 'POP', 'LDM', 'STM', 'LDMIA', 'LDMDB', 'LDMFD', 'LDMEA', 'STMIA', 'STMDB', 'STMFD', 'STMEA', 'ADR', 'WFE', 'WFI', 'DMB', 'DSB', 'ISB', 'MRS', 'MSR', 'NOP', 'SEV', 'SVC', 'CLZ', 'CMP', 'CMN', 'MOVT', 'REV', 'REV16', 'REVSH', 'RBIT', 'SADD16', 'SADD8', 'SHADD16', 'SHADD8', 'SHASX', 'SHSAX', 'SHSUB16', 'SHSUB8', 'SSUB16', 'SSUB8', 'SASX', 'SSAX', 'TST', 'TEQ', 'UADD16', 'UADD8', 'UASX', 'USAX', 'UHADD16', 'UHADD8', 'UHASX', 'UHSAX', 'UHSUB16', 'UHSUB8', 'USAD8', 'USADA8', 'USUB16', 'USUB8', 'UMULL', 'UMAAL', 'UMLAL', 'SMLAD', 'UMULL', 'UMLAL', 'SMULL', 'SMLAL', 'SDIV', 'UDIV', 'SSAT', 'USAT', 'SSAT16', 'USAT16', 'QADD', 'QSUB', 'QASX', 'QSAX', 'QDADD', 'QDSUB', 'UQASX', 'UQSAX', 'UQADD', 'UQSUB', 'PKHBT', 'PKHTB', 'SXT', 'UXT', 'SXTB', 'UXTB', 'SXTH', 'UXTH', 'SXTB16', 'UXTB16', 'SXTA', 'UXTA', 'SXTAB', 'UXTAB', 'SXTAH', 'UXTAH', 'SXTAB16', 'UXTAB16', 'BFC', 'BFI', 'SBFX', 'UBFX', 'SXT', 'UXT')
oper_s_cond = ('ADD', 'ADC', 'SUB', 'SBC', 'RSB', 'AND', 'ORR', 'EOR', 'BIC', 'ORN', 'ASR', 'LSL', 'LSR', 'ROR', 'RRX', 'MOV', 'MVN', 'MUL', 'MLA', 'MLS')
oper_xy_cond = ('SMLA', 'SMLAW', 'SMLAL', 'SMLALD', 'SMLSD', 'SMLSLD', 'SMMLA', 'SMMLS', 'SMMUL', 'SMUAD', 'SMUSD', 'SMUL', 'SMULW')
oper_type_cond = ('LDREX', 'STREX')
oper_LDR_type_T_cond = ('LDR',)
oper_STR_type_T_cond = ('STR',)
oper_branch_cond_register = ('BLX', 'BX')
oper_branch_cond_label = ('BL', 'B')
oper_IT = ('IT',)
oper_stack = ('POP', 'PUSH')
oper_mem = ('LDR', 'STR')
directive = ('MACRO', 'ENDM', 'SYNTAX', 'THUMB', 'CPU', 'FPU', 'EQU', 'INCLUDE', 'INCBIN', 'SECTION', 'ALIGN', 'GLOBAL', 'WEAK', 'SET', 'ARM', 'CODE16', 'CODE32', 'FORCE_THUMB', 'THUMB_FUNC', 'LTORG', 'ORG')
directive_include = ('INCLUDE', 'INCBIN')
WORD = ('WORD', 'HWORD', 'BYTE', 'SHORT', 'SPACE', 'ASCII', 'ASCIZ', )

op_1 = (oper + oper_cond + oper_s_cond + oper_xy_cond + oper_type_cond + oper_LDR_type_T_cond + oper_STR_type_T_cond + oper_branch_cond_register + oper_branch_cond_label + oper_IT)
position = 0
last_oper = ""
after_label = 0
bracket = 0
#####################
include_file = {} 		# библиотека с инклудами текущего файла
include_global = {}
auto_modus = 0
##################### настройка отступа от начала строки ###################
shift_1 = 20
shift_2 = 28
bracket_schift = 0
macros = 0
macros_shift = shift_2 - shift_1 + 4
asm_files = ("ASM", "S")

#####################
class IncludeFileCommand(sublime_plugin.TextCommand): 	# копируем файл в каталог <inc>
	def run(self, edit, text):							# если каталога нет, создаем его
		path_temp = text.split("\\")					# в <text> передается адрес файла
		
		filename = path_temp[-1] 						# имя импортируемого файла
		path_temp = path_temp[:-1]
		path_from = ""
		for i in path_temp:
			path_from += i + "\\" 						# путь откуда импортируем
		
		path = self.view.file_name() 					# текущее положение файла <.asm>
		path = path.split("\\")[:-1]
		bibl_name = path[-1]							# имя текущей папки

		directory = ""
		for i in path:
			directory += i + "\\" 						# текущая папка файла <.asm>

		path = directory + "inc\\"

		try:
			os.mkdir(path) 								# создаем папку <inc> если ее нет
		except:
			None

		cursor_pos = self.view.sel()[0].begin() 		# текущая координата курсора
		
		if "main" not in filename and path_from != path:
			shutil.copy2(text, path)

			if path_from == directory:
				os.remove(text) 			# удаляем файл, если он находится в корневом каталоге проекта
			
			if bibl_name not in include:						# если бибилиотеки еще нет в {include}
				exec(f"{bibl_name} = {{}}", globals())			# создаем библиотеку для include
				include[bibl_name] = eval(bibl_name)				# помещаем новую библиотеку в include

			import_include(f"{path}\\{filename}", include[bibl_name]) 	# импортируем файл в библиотеку <include>

			if ".INC" not in filename.upper():
				self.view.insert(edit, cursor_pos, text=f'"{path}{filename}"')
			else:
				line_start = self.view.line(cursor_pos)
				text = int(shift_1/4) * "\t"
				self.view.replace(edit, line_start, text=text)
				sublime.message_dialog(f" Include file <{filename}> was copy to <\\inc> and \n successfully import in project !")
		else:
			self.view.insert(edit, cursor_pos, text=f'"Can not import <{filename}> file !!!"')


#####################
class ImportEquCommand(sublime_plugin.TextCommand):  # глобальные переменные для всего проекта
	def run(self, edit):
		global include
		global include_global
		include_global = {}

		###################
		views = sublime.active_window().views() 	# Список открытых файлов в Sublime Text 
		for view in views:
			current_view = view.file_name() 			# получаем адрес открытого файла
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
		
				

		
#####################
class ImportSetCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global include_file
		global include
		include_file = {}
		
		text = self.view.substr(sublime.Region(0, self.view.size())) 	# str
		text = text.split("\n")

		path = self.view.file_name() 				# текущее положение файла <.asm>
		path = path.split("\\")
		filename = path[-1]							# имя файла
		bibl = f"{path[-2]}_{filename}" 			# имя библиотеки в include

		for line in text:
			
			# обработка <.SET>
			if ".set" in line or ".SET" in line:
				line = line.replace(",", "").split("@")
				if len(line) == 1:
					line.append("")
				comment = line[1]
				line = line[0].split(" ")[1:]
				try:
					try:
						include_file[line[0]] = [int(line[1]), f"{hex(int(line[1]))}", comment + " <.set>"]
					except:
						include_file[line[0]] = [int(line[1], 16), f"{line[1]}", comment + " <.set>"]
				except:
					include_file[line[0]] = [">>", f"{line[1]}", comment + " <.set>"]
			
			
			elif len(line) > 1:
				# обработка <.MACRO>
				if ".macro" in line or ".MACRO" in line:
					line = line.split(" ")
					line[1] = line[1].replace("\n", "")						
					include_file[f"{line[0]} {line[1]}"] = ["", f"{line[1]}",  f"<macros>"]

				# обработка label
				elif line[0] != "\t" and line[0] != "." and ":" in line:
					line = line.split(":")
					temp = line[1].split(" ")
					line[1] = ""

					for item in temp:
						item = item.replace(" ", "").replace("\t", "")
						if len(item) > 0:
							line[1] += (item) + " "
					
					if len(line[1]) > 0:
						line[1] = f"{line[1]}"
					
					
					include_file[line[0]] = ["", line[1],  "<label>"]
								
		
		bibl_set = bibl + "_set"
		include[bibl_set] = include_file				# добавили библиотеку _set в основной {include}	
					


#####################
class EventListener(sublime_plugin.EventListener):
	def on_text_command(self, view, command_name, args):
		global auto_modus

		try:
			if command_name == "insert":
				symbol = args["characters"]

				if symbol == "\n":
					view.run_command('new_line_correct')
			
			if command_name == "auto_complete":
				auto_modus = 0
				view.run_command('import_equ')

			elif command_name == "toggle_record_macro":
				auto_modus = 1
				# считать все .set и label: в текущем файле
				view.run_command('import_set')
				view.run_command('auto_complete')
				
			elif command_name == "run_macro_file":
				view.run_command('new_line_correct')

					
		except:
			None

	def on_post_text_command(self, view, command_name, args):
		global after_label
		global position
		global last_oper
		
		try:
			if command_name == "insert":
				symbol = args["characters"]

				if symbol == "\n":
					after_label = 0
					position = 0
					last_oper = ""
					view.run_command('new_line')
					
		except:
			None

	def on_query_completions(self, view, prefix, locations):
		global auto_modus
		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]

		if syntax == "Assembler_GNU":

			completions = sublime.CompletionList()
			items = []
			
			path = view.file_name() 					# текущее положение файла <.asm>
			path = path.split("\\")
			filename = path[-1]							# имя файла
			bibl = path[-2] 		                	# имя библиотеки в include
						
			if auto_modus == 1:
				bibl_set = f"{bibl}_{filename}_set"
				bibliothek = include[bibl_set]
			else:
				bibl_global = bibl + "_global"
				bibliothek = {**include[bibl], **include[bibl_global]}
			
			
			# элементы списка
			for keys in bibliothek:
				if prefix in keys or prefix.upper() in keys:
					items.append(
						sublime.CompletionItem(
							trigger=f"{keys}: {(20 - len(keys)-len(str(bibliothek[keys][0])))*' '}{bibliothek[keys][0]}  ({bibliothek[keys][1]})",
							completion=f"{keys.replace('.GLOBAL ', '').replace('.global ','').replace('.MACRO ', '').replace('.macro ','')}",
							annotation=f"{bibliothek[keys][2]}",								
							)
						)
							
			completions.set_completions(items, flags=sublime.DYNAMIC_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
			
			return completions
			
					
	def on_load(self, view):   # Вызывается при загрузке файла в буфер
		current_view = view.file_name() 			# получаем адрес открытого файла
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
		if bibl_name not in include:
			
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
		

#####################
class NewLineCorrectCommand(sublime_plugin.TextCommand): # обработка текущей строки при нажатии enter
	def run(self, edit):
		global bracket
		global bracket_schift
		global macros

		####################
		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]

		if syntax == "Assembler_GNU":
			cursor_pos = self.view.sel()[0].begin()
			word_region = self.view.word(cursor_pos) 		# координаты слова перед курсором
			current_word = self.view.substr(word_region) 	# активное слово
			current_word_up = current_word.upper() 			# активное слово ЗАГЛАВНОЕ
			bevor_word_region = self.view.word(cursor_pos-1)
			bevor_word = self.view.substr(bevor_word_region)
			bevor_word_up = bevor_word.upper()
			

			if current_word_up in register:
				self.view.replace(edit, word_region, text=current_word_up)
			elif bevor_word_up in register:
				self.view.replace(edit, bevor_word_region, text=bevor_word_up)


			line_start = self.view.line(cursor_pos) 		# координаты строки
			current_line = self.view.substr(line_start)     # содержание строки
			current_line_up = current_line.upper() 			# строка ЗАГЛАВНЫЕ
			current_directive_line = current_line_up.replace("\t", "") # строка заглавная без \t

			macro_check = current_directive_line.split(" ")[0]
			if "(" in macro_check:
				macro_check = 1
			else:
				macro_check = 0
			
			line_befor_cursor = sublime.Region(line_start.a, cursor_pos)	
			current_line_cursor = self.view.substr(line_befor_cursor) 		# содержание строки до курсора
						
			if "(" in current_line_cursor and macro_check != 1:
				for i in range(len(current_line_cursor)):
					if current_line_cursor[i] == "(":
						bracket_schift = i
						break
				bracket = 1

				current_line = current_line.replace("(", "( ").replace("(  ", "( ")
				
			if "=" in current_line:
				current_line = current_line.replace("=", "= ").replace("=  ", "= ")

			if "|" in current_line:
				current_line = current_line.replace("|", "| ").replace("|", " |").replace("|  ", "| ").replace("  |", " |")
			
			if "+" in current_line:
				current_line = current_line.replace("+", "+ ").replace("+", " +").replace("+  ", "+ ").replace("  +", " +")

			if "*" in current_line:
				current_line = current_line.replace("*", "* ").replace("*", " *").replace("*  ", "* ").replace("  *", " *")
			
			if "/" in current_line and "head" not in current_line:
				current_line = current_line.replace("/", "/ ").replace("/", " /").replace("/  ", "/ ").replace("  /", " /")

			if "-" in current_line and current_directive_line[0] != "." and "POP" not in current_line and "PUSH" not in current_line:
				current_line = current_line.replace("-", " - ").replace(",", ", ").replace(",  ", ", ").replace("  -  ", " - ")

			if ")" in current_line_cursor and macro_check != 1:
				bracket = 2
				current_line = current_line.replace(")", " )").replace("  )", " )")
							
			if current_word == ":\n" or current_word == ":":
				current_line = current_line.replace("\t", "").replace(" ", "") + " "
			
			if position == 99: 		# обработка ввода команд стека
				current_line = current_line.upper()

			if "POP" in current_line or "PUSH" in current_line:
				current_line.replace("r", "R").replace("l", "L").replace("s", "S").replace("i", "I").replace("p", "P").replace("c", "C")

						
			try:
				if current_directive_line[0] == "." and current_word_up in directive:
					
					stroka = current_directive_line.split(" ")

					if (len(stroka)) == 1:
						current_line = current_directive_line

				if current_word_up in directive_include: 	# обработка команды <include>
					self.view.insert(edit, cursor_pos, text=" ")
					path = self.view.file_name()
					path = path.split("\\")[:-1]
					directory = ""
					for i in path:
						directory += i + "\\"

					sublime.open_dialog(callback=self.FilePath,file_types=[("Include Files", ["asm", "s", "bin", "inc"])],
									directory=directory)	
								
			except:
				None
			
			if ".MACRO" in current_line:
				macros = 1

			if ".ENDM" in current_line:
				macros = 0

			self.view.replace(edit, line_start, text=current_line)

	############
	def FilePath(self, path):
		self.view.run_command('include_file', {"text":path})



#####################
class NewLineCommand(sublime_plugin.TextCommand): # выравнивание следующей строки по (shift_1/4)
	def run(self, edit):
		global bracket
		global bracket_schift
		global macros
		###########################
		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]

		if syntax == "Assembler_GNU":
			cursor_pos = self.view.sel()[0].begin()
			line_start = self.view.line(cursor_pos)

			current_line = self.view.substr(line_start) 					# содержание строки
			line_befor_cursor = sublime.Region(line_start.a, cursor_pos)	
			current_line_cursor = self.view.substr(line_befor_cursor) 		# содержание строки до курсора
			
			leng_line = len(current_line_cursor)
			
			if "\t" not in current_line_cursor:
				no_tab = 1
			else: no_tab = 0
							
			shift = ""
			
			if macros == 1:
				if leng_line == 0:
					shift = "\t"

			elif leng_line == 0 or no_tab == 1:
				if macros == 0:
					shift = int(shift_1/4) * "\t"
			
			if bracket == 1 and leng_line == int(shift_1/4) + 1:
				shift += (bracket_schift - 4) * " " 
			elif bracket == 1 and leng_line == int(shift_1/4):
				shift += (bracket_schift) * " " 
				
			elif bracket == 2:
				bracket = 0
							
				
			self.view.insert(edit, line_start.a, text=shift)


#####################
class SpacerCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global after_label
		global position
		global last_oper
		global include_path
############################
		cursor_pos = self.view.sel()[0].begin() 	# текущая координата курсора
######################################################
		self.view.insert(edit, cursor_pos, " ") 	# вставляем стандартный пробел
######################################################
		self.edit = edit
		word_region = self.view.word(cursor_pos) 			# координата начала слова перед курсором
		bevor_word_region = self.view.word(cursor_pos-1) 	# координата предыдущего слова
		line_start = self.view.line(cursor_pos) 			# координата начала строки

		
		syntax = (sublime.active_window().active_view().settings().get('syntax')).split("/")[-1].split(".")[0]
		if syntax == "Assembler_GNU":
			
			current_word = self.view.substr(word_region) 		# активное слово
			bevor_word = self.view.substr(bevor_word_region) 	# предыдущее слово
			current_line = self.view.substr(line_start) 		# содержимое всей строки
			current_line_up = current_line.upper() 				# содержимое строки ЗАГЛАВНЫЕ буквы
			current_word = current_word.upper()
			bevor_word = bevor_word.upper()

			directive_line = current_line_up.replace("\t", "") 		# если директивы в строке еще не было
			if directive_line[0] == "." and current_word in directive:
				self.view.replace(edit, line_start, text=directive_line)

			
			if current_word in directive_include: 	# обработка команды <include>
				path = self.view.file_name()
				path = path.split("\\")[:-1]
				directory = ""
				for i in path:
					directory += i + "\\"

				sublime.open_dialog(callback=self.FilePath,file_types=[("Include Files", ["asm", "s", "bin", "inc"])],
									directory=directory)	
								

			between_region = sublime.Region(line_start.a, word_region.a) 	# регион между началом строки и словом
			between_word = self.view.substr(between_region)

			bevor_clear = not any(a.isalnum() for a in between_word) 		# если слово первое в строке
			
			word_to_start = current_word[0]

			if (cursor_pos + 1) == line_start.b: 	# после курсора нет символов
				not_more_after = 1
			else: not_more_after = 0
			

			if bevor_clear or word_to_start == ":" or after_label == 1:
			 	# если начало строки или после label
				# если введен label:
				if word_to_start == ":":
					if not_more_after == 1:
						current_line = current_line.replace("\t", "").replace(" ", "") + " "
						self.view.replace(edit, line_start, text=current_line)
						after_label = 1
											
					self.RemoveCursor(shift_1)

				
				for item in op_1:
					if item in current_word:
						if current_word[:len(item)] == item:
							self.view.replace(edit, word_region, text=current_word + " ")
							if macros == 1:
								self.SetCursor(macros_shift)
							else: 
								self.SetCursor(shift_2)

							after_label = 0
							position = 1
							last_oper = item
							if last_oper in oper_stack:
								pos = self.view.sel()[0].a
								self.view.insert(edit, pos, text="{}")
								self.view.sel().clear()
								self.view.sel().add(pos+1)
								position = 99
							break

				if current_word in WORD:
					shift = shift_2 - shift_1 - len(current_word) - 2
					shift = shift * " "
					self.view.replace(edit, word_region, text=(current_word + shift))
				
			
			else:
				
				if position == 1:
					
					if current_word in register and last_oper not in oper_branch_cond_register:
						self.view.replace(edit, word_region, text=current_word + ",")
						position = 2
					elif bevor_word in register:
						self.view.replace(edit, bevor_word_region, text=bevor_word)
						position = 2
					if last_oper in oper_mem and current_word in register: 	# если запись идет в адрес
						pos = self.view.sel()[0].a
						self.view.insert(edit, pos, text="[]")
						self.view.sel().clear()
						self.view.sel().add(pos+1)

				elif position == 2:
					if current_word in register:
						self.view.replace(edit, word_region, text=current_word)
						position = 3
					elif bevor_word in register:
						self.view.replace(edit, bevor_word_region, text=bevor_word)
						position = 2
		
############
	def FilePath(self, path): 	# устанавливаем допустимый формат фалов на импорт
		check = path.upper()
		flag = 0
		files = (".INC", ".ASM", ".S", ".BIN")
		for i in files:
			if i in check:
				flag = 1
				break
			else:
				flag = 0
		if flag == 1:
			self.view.run_command('include_file', {"text":path})
		else:
			sublime.error_message(f" File extension is not support ! \n only {files} can be import")


############
	def SetCursor(self, shift=0): 	# установка курсора в нужное место относительно начала строки через " "
		global after_label
		cursor_pos = self.view.sel()[0].begin()
		shift_coord = self.view.line(cursor_pos)
		
		word_coord = self.view.word(cursor_pos-2)
		current_line = self.view.substr(shift_coord)

		if "\t" not in current_line:
			shift_correct = -1
		else:
			shift_correct = 0

		for i in current_line:
			if i == "\t": shift_correct += 4
			else: shift_correct += 1
							
				
		word_leng = word_coord.b - word_coord.a
		space = shift - shift_correct
		if after_label == 1: space -= 1
		space = " " * space

		self.view.insert(self.edit, shift_coord.b, text=space)

	def RemoveCursor(self, shift=0): 	# выравнивание курсора после : относительно начала строки через " "
		cursor_pos = self.view.sel()[0].begin()
		line_start = self.view.line(cursor_pos)
		current_line = self.view.substr(line_start)
		leng_line = len(current_line)

		leng_label = 0
		i = 0
		for i in range(leng_line):
			if current_line[i] == " ":
				leng_label = i
				break

		for i in range(i, leng_line):
			if current_line[i] == " ":
				leng_label += 1
			else: break

		current_label = current_line[:leng_label].replace(" ", "")
		current_line = current_line[leng_label:]

		space = shift - len(current_label)
		if space >= 0:
			current_label += " " * space
		else:
			current_label += " "

		current_line = current_label + current_line
		self.view.replace(self.edit, line_start, text=current_line)




		#temp = ["RCC_ACR", "RCC_CFGR", "RCC_CR"]
		#sublime.active_window().active_view().show_popup_menu(temp, 0)


#########################
