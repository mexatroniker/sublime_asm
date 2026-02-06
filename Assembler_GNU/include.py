import sublime
import sublime_plugin
import os

terminal = sublime.active_window().create_output_panel('info_panel')
terminal.assign_syntax("Assembler_GNU.sublime-syntax")

include = {} 						# библиотека {include} содержит несколько словарей для каждого проекта ASM
path_list = [] 						# пути к файлам ASM
asm_files = ("ASM", "S")

################
def print_terminal(text): 				# Вывод текста в Output Panel
	global terminal
	terminal.run_command('append', {'characters': f"{text}\n"})
	sublime.active_window().run_command('show_panel', {'panel': 'output.info_panel'})


##############
def import_include(path_file, bibl_name): 		# Функция импорта include из файла с адресом <path_file>
	global terminal
	with open (path_file, 'r', encoding='utf-8') as file:
		clock = 0  					# допустимое количество пустых строк в фале <include> = 10 см.ниже
		line_nummer = 0
		values = 0
		file_include = path_file.split("\\")[-1]

		while(1):
			line_nummer += 1
			stroka = file.readline()
			stroka = stroka.replace("@", " @").replace(",", " ")
			
			if (len(stroka)) == 0:
				clock += 1
				if clock == 10: break
			else:
				clock = 0

			stroka = stroka.split("@")
			
			if len(stroka) == 1:
				stroka.append("")
				
			stroka_value = stroka[0]
			
			try:
				stroka_comment = stroka[1]
			except:
				None
			
			stroka = []
			temp = ""
			for i in stroka_value:
				if i  == "\n":
					stroka.append(temp)
					break

				if i != " ":
					temp += i
				else:
					if len(temp) > 0:
						stroka.append(temp)
						temp = ""
			
			try:
				if ".equ" in stroka or ".EQU" in stroka or "#define" in stroka or "#DEFINE" in stroka:
					
					stroka_leng = len(stroka)
					
					for i in range(3, stroka_leng):
						stroka[2] += stroka[i]

					stroka = stroka[1:3]
					stroka.append(stroka[1])
					stroka[0] = stroka[0].replace(",", "")
					# list[0] = name
					# list[1] = value
					
				
					stroka[2] = f"{hex(eval(stroka[2]))}"		# делаем вычисления в ячейке, если там не только значение
					exec(f"{stroka[0]} = {stroka[2]}") 		# создаем переменную
					stroka.append(stroka_comment)
					stroka[1] = f"{int(stroka[2],16)}"
					bibl_name[stroka[0]] = stroka[1:4]		# добавляем в словарь [0]=name, [1]=string, [2]=value, [3]=comment
					values += 1
				
						
			except SyntaxError:
				print_terminal(f'>> <{file_include}> <line {line_nummer}> - ErrorSyntax: {stroka[2]}')

			except IndexError:
				print_terminal(f'>> <{file_include}> <line {line_nummer}> - ErrorIndex: {stroka}')

			except ValueError:
				print_terminal(f'>> <{file_include}> <line {line_nummer}> - ErrorValue:')

			except NameError:
				print_terminal(f'>> <{file_include}> <line {line_nummer}> - ErrorName: {stroka[2]}')
			
			

	print_terminal("------------------")			
	print_terminal(f'>> From "{path_file}" saved {values} values from {line_nummer-9} lines')

###############		


views = sublime.active_window().views() 	# Список открытых файлов в Sublime Text 
											# процедура запускается один раз при запуске программы Sublime
											# импортирует файлы <.inc> если они находятся в одном каталоге
											# с открытым файлом <asm_files> и сохраняет в {include}

for view in views:
	current_view = view.file_name() 			# получаем адрес открытого файла
	current_view = current_view.split("\\")
	
	file_name = current_view[-1]
		
	try:
		file_name = file_name.split(".")[-1].upper()
	except:
		file_name = "None"

	if file_name in asm_files: 					# если файл имеет расширение из <asm_files>
		current_view = current_view[:-1]

		current_path = ""
		for i in current_view:
			current_path += i + "\\"

		if current_path not in path_list:
			path_list.append(current_path) 				# получили список путей файлов <.asm>

		

######################
#path = os.path.abspath(__file__)
#path_directory = os.path.dirname(path)
######################

for file_asm in path_list: 							# проходимся по каждому адресу из открытых файлов
	path = [file_asm]
	bibl_name = file_asm.split("\\")[-2]			# имя папки проекта = имя библиотеки {include}
	exec(f"{bibl_name} = {{}}", globals())			# создаем библиотеку для include
	include[bibl_name] = eval(bibl_name)			# помещаем новую библиотеку в include
	#(WB55_SUBLIME)
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


