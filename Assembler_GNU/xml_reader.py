# Считываение XML файла в словарь bibl
import copy

###################
def xml_to_bibl(path):
	bibl = {}

	with open (path, 'r', encoding='utf-8') as file:
		file_name = path.split("\\")[-1].split(".")[0]
		
		while(1):
			stroka = file.readline()
			if "<peripherals>" in stroka: break

		while(1):
			stroka = file.readline()
			###############
			if "<peripheral>" in stroka or "<peripheral derived" in stroka:

				flag_name = 0
				flag_description = 0
				flag_baseaddress = 0
				flag_group = 0
				flag_derived = 0
				derived_from = ""


				if "derived" in stroka:  		# если регистры копируются из другой перефирии
					flag_derived = 1
					derived_from = stroka.split("=")[1].replace('"', "").replace(">", "").replace("\n","")
					

				while(1):
					temp_stroka = file.readline().replace("\t", "").replace("\n", "")
					stroka = ""
					i = 0
					for i in range(len(temp_stroka)):
						if temp_stroka[i] == "<": break
						stroka = temp_stroka[i+1:]

					if "<name>" in stroka and flag_name == 0:
						stroka = stroka.replace("<name>", "").replace("</name>", "")
						name = stroka
						flag_name = 1
				
					elif "<description>" in stroka and flag_description == 0:
						stroka = stroka.replace("<description>", "").replace("</description>", "")
						description = stroka
						flag_description = 1
						
					elif "<groupName>" in stroka and flag_group == 0:
						stroka = stroka.replace("<groupName>", "").replace("</groupName>", "")
						group = stroka
						flag_group = 1

					elif "<baseAddress>" in stroka and flag_baseaddress == 0:
						stroka = stroka.replace("<baseAddress>", "").replace("</baseAddress>", "")
						baseaddress = stroka
						flag_baseaddress = 1

						if flag_derived == 1: 			# если регистры копируется из другой переферии							
							group = name

							for key in bibl: 			# узнали название группы
								if derived_from in bibl[key]:
									group = key	
									break

							register = copy.deepcopy(bibl[group][derived_from])
							register["baseaddress"] = baseaddress
							register_group = {}														
							register_group[name] = register							
							bibl.setdefault(group, {}) 	# если группа отсутствует то она создастся
							bibl[group].update(register_group)

							break

					elif "<registers>" in stroka:
						register_group = {}
						register = {}
						if flag_description == 0:
							description = "No description"
						register["description"] = description
						register["baseaddress"] = baseaddress						
						register_group[name] = register
						if flag_group == 0:
							group = file_name 			# если нет названия группы -> берется название файла
						bibl.setdefault(group, {})
						bibl[group].update(register_group)	
						break
			
			#################
			if "<register>" in stroka:

				flag_register_name = 0
				flag_addressoffset = 0				

				while(1):
					temp_stroka = file.readline().replace("\t", "").replace("\n", "")
					stroka = ""
					i = 0
					for i in range(len(temp_stroka)):
						if temp_stroka[i] == "<": break
						stroka = temp_stroka[i+1:]
					
					if "<name>" in stroka and flag_register_name == 0:
						stroka = stroka.replace("<name>", "").replace("</name>", "")
						register_name = stroka
						flag_register_name = 1

					elif "<addressOffset>" in stroka and flag_addressoffset == 0:
						stroka = stroka.replace("<addressOffset>", "").replace("</addressOffset>", "")
						addressoffset = stroka
						flag_addressoffset = 1

					elif "<fields>" in stroka:
						register = {}
						register["addressoffset"] = addressoffset
						bibl[group][name][register_name] = register						
						
						while(1):
							temp_stroka = file.readline().replace("\t", "").replace("\n", "")
							stroka = ""
							i = 0
							for i in range(len(temp_stroka)):
								if temp_stroka[i] == "<": break
								stroka = temp_stroka[i+1:]
							
							if "<name>" in stroka:
								stroka = stroka.replace("<name>", "").replace("</name>", "")
								field_name = stroka
							
							elif "<description>" in stroka:
								stroka = stroka.replace("<description>", "").replace("</description>", "")
								field_description = stroka

							elif "<bitOffset>" in stroka:
								stroka = stroka.replace("<bitOffset>", "").replace("</bitOffset>", "")
								field_bitoffset = stroka

							elif "<bitWidth>" in stroka:
								stroka = stroka.replace("<bitWidth>", "").replace("</bitWidth>", "")
								field_bitwidth = stroka

							elif "</field>" in stroka:
								field = {}								
								field["description"] = field_description
								field["bitoffset"] = field_bitoffset
								field["bitwidth"] = field_bitwidth
								bibl[group][name][register_name][field_name] = field

							elif "</fields>" in stroka:
								break

						break

								
			if "</peripherals>" in stroka:
				break
	
	return bibl
