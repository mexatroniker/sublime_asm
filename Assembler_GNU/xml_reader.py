# Считываение XML файла в словарь bibl

###################
def xml_to_bibl(path):
	bibl = {}

	with open (path, 'r', encoding='utf-8') as file:
		while(1):
			stroka = file.readline()
			if "<peripherals>" in stroka: break

		while(1):
			stroka = file.readline()
			###############
			if "<peripheral>" in stroka:

				flag_name = 0
				flag_description = 0
				flag_baseaddress = 0
				flag_group = 0

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

					elif "<registers>" in stroka:
						register_group = {}
						register = {}
						register["description"] = description
						register["baseaddress"] = baseaddress
						register_group[name] = register
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
