### The GNU Assembler plugin for Sublime Text 4
---
The plugin can be use in **Sublime Text 4** for program in **GNU Assembler** language for microcontrollers.  
This plugin includes all the necessary tools for preparing firmware for a microcontroller, compiling it, and uploading it to flash memory.  

---
### Install:
* Run the **git clone** command into the &lt;Packages&gt; folder of your installed **Sublime text 4** editor:  
&ensp; 1. In Sublime text: >> Menu/Preferences/Browse Packages...  
&ensp; 2. **Without** preliminary initialization of the folder using the <`git init`> -  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; run command <`git clone https://github.com/mexatroniker/sublime_asm.git .`>  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; *Note the &lt;**.**&gt; at the end of the command line.  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; This will allow you to copy files to the necessary directory without creating a separate project folder.*  
 
* You can also click the **Code** button and then **Download ZIP**. Unpacking the archive to your packages folder:  
Sublime text: >> Menu/Preferences/Browse Packages...  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*Note that the* &lt;Packages&gt; *folder should contain the only project files, and  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;not a folder called &lt;**sublime_asm-main**&gt;*
---
### Features:
* It is allowed to use files in UTF-8 encoding
* If you already have a project created in another editor or have indents configured in spaces, then before using it you need to run the command: **Ctrl+Shift+P** -> **Indentation: Convert to Tabs**
* The plugin allows you to create a full-fledged project written in GNU Assembler. The plugin includes all the necessary files for compiling the project in the **.bin** and **.hex** formats, followed by flashing it into the microcontroller's flash memory using Openocd https://openocd.org/
* By writing a project, the plugin automatically formats syntax and highlights command directives and values
* It is possible to specify inclides files for the entire project. To use the necessary files, they must be located either in the project folder or in the **/inc** folder. You can also add files using the editor. To do this, enter the **.INCLUDE** directive, after that pressing the Space or Enter, you will be prompted to select the required file in the file system. After this, it will be automatically copied to the **/inc** folder and will be immediately available for use. The include format allows the use of not only the **.EQU** directive, but also the **#define** , which allows the use of files from other programming languages. They are available for selection with the < **Ctrl+Space** > combination
* Any include declared in any project file via **.EQU** will be immediately accessible from any other project file
* Comments in project files can begin with symbols: < **@ ; #** >
* Declared in each file includes by the **.SET** directive, and macros and address labels are available for selection with the < **Ctrl+Q** > combination
* Can also add the macros and other necessary variables anywhere in the files, including after the text of the main program text
* To insert a large number of values for one command line, it is possible to wrap the input to the next line. To do this, you need to enclose the value in brackets ( ... | ... | ... )
* Each project file is compiled separately, so the microcontroller core type, syntax variant, and so on must be specified separately for each file. For ease of use, the necessary information can be entered only in the < **main.asm** > file. All lines entered within the < **head** > ... < **/head** > will be automatically added to all other project files
* To assemble the project, use the key combination < **Ctrl+E** >. After this, if there are no errors in the project folder, a **/bin** folder will be created, which will contain the **.bin** and **.hex** firmware files
* To write to the microcontroller's flash memory, you must first configure commands for Openocd.  
* For this, the < **openocd.bat** > file is present in each the project folder, in which you must specify the type of microcontroller used by the programmer, as well as the programming commands, for example:
<div align="center">
<img src="https://github.com/mexatroniker/mexatroniker/blob/main/openocd.jpg" alt="openocd.bat" width="500" align="center">
</div>  

*Please note: This file will not be run for firmware installation. It simply specifies the necessary commands, so the file format cannot be changed. It also cannot contain more than five blank lines. A line beginning with a < **-** > sign will be added to the final project launch file. The string < **bin/project.bin** > should also not change - this is just the path to the folder with the **.bin** file*  
* To assemble the project and flash the microcontroller, use the combination < **Ctrl+Shift+E** >
---
### TODO:
* [ ] Debug microcontrollers firmware 
---
### Support:
* If you have any questions or wishes, you can ask them in the Telegram group:  
&ensp;&ensp;&ensp;&ensp;<img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="16" height="16">&ensp;&ensp;https://t.me/sublime_asm
* You can also find example of GNU Assembler project in my repository
---
### Respect:
* I would like to express my respect to **Vitaly Gorbukov** for explaining the principles of GNU Assembler, as well as for creating his editor "Assembler Editor Plus". If you want to know more about this:  
	* https://habr.com/ru/users/VitGo/
	* https://www.youtube.com/@vitgo

