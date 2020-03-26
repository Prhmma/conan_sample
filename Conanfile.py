import os
import subprocess
from conans import ConanFile, CMake
from subprocess import Popen

class ToolchainTesting(ConanFile):
  settings = (
    "os",
    "compiler",
    "build_type",
    "arch"
  )

  requires = (
    "CMake/3.3.2@epen/stable",
    "mingw/7.1.0@epen/stable"
  )

  generators = (
    "virtualenv"
  )

  project_name = "SystemCommon"

  def system_requirements(self):
    BAT_ENV = 'environment.bat.env'
    SH_ENV  = 'environment.sh.env'
    MINGW_ENV = 'environment.mingw.env'
    BAT_ACT = 'activate.bat'
    SH_ACT = 'activate.sh'
    MINGW_ACT = 'activate_mingw.sh'
    buildDir = os.getcwd()

    batEnvFilename = os.path.join(buildDir, BAT_ENV)
    shEnvFilename = os.path.join(buildDir, SH_ENV)
    mingwShEnvFilename = os.path.join(buildDir, MINGW_ENV)
    batFilename = os.path.join(buildDir, BAT_ACT)
    shFilename = os.path.join(buildDir, SH_ACT)
    mingwShFilename = os.path.join(buildDir, MINGW_ACT)

    if os.path.exists(batFilename):
        with open(batFilename, "r+") as batFile:
            old = batFile.read()  # read everything in the file
            batFile.seek(0)  # rewind
            batFile.write('@SET CLICOLOR_FORCE=1\n')
            batFile.write('@SET GTEST_COLOR=1\n')
            batFile.write(old)
            batFile.truncate()

    if os.path.exists(shFilename):
        with open(shFilename, "r+") as shFile:
            old = shFile.read()  # read everything in the file
            shFile.seek(0)  # rewind
            shFile.write('export CLICOLOR_FORCE=1\n')
            shFile.write('export GTEST_COLOR=1\n')
            shFile.write(old)
            shFile.truncate()

    # Using activate.sh in a MinGW environment (e.g. git bash) leads to the following problem.
    # On a Linux system multiple paths in the PYTHONPATH variable are separated by colons (PYTHONPATH="path1":"path2":"path3"), but
    # MinGW passes these multiple paths as one path to Python. In order that MinGW passes multiple paths to Python, the PYTHONPATH
    # variable has to be changed to PYTHONPATH="path1;path2;path3", the following code does this and generates a new script
    # 'activate_mingw.sh' with this new PYTHONPATH.
    # Conan 1.21 removed the environment varibale definitions from the activate.* files, they can now be found in corresponding
    # environment.*.env files. If these are present, perform the PYTHONPATH modifications there.
    if self.settings.os == "Windows":
        if os.path.exists(shEnvFilename) and os.path.exists(shFilename):
            # create a mingw env file from the shell, replacing the PYTHONPATH with a ';'-separated version
            with open(shEnvFilename, "r") as shEnvFile, open(mingwShEnvFilename, 'w+') as mingwEnvFile:
                for line in shEnvFile:
                    if "PYTHONPATH" in line:
                        pythonpath = line.replace('":"', '"\\;"')
                        pythonpath = pythonpath.replace('${PYTHONPATH+:$PYTHONPATH}', '${PYTHONPATH+;$PYTHONPATH}')
                        mingwEnvFile.write(pythonpath)
                    else:
                        mingwEnvFile.write(line)

            # create 'activate_mingw.sh' that uses the mingw env file
            with open(shFilename, "r") as shFile, open(mingwShFilename, "w+") as mingwShFile:
                for line in shFile:
                    line = line.replace(SH_ENV, MINGW_ENV)
                    mingwShFile.write(line)

        elif os.path.exists(batFilename) and os.path.exists(shFilename):

            # Read the ;-separated PYTHONPATH variable from the batch file
            with open(batFilename, "r") as batFile:
                for line in batFile:
                    if "PYTHONPATH" in line:
                        pythonpath = line.split('=')[1].split('%')[0]
                        break

            # Create 'activate_mingw.sh' with ;-separated PYTHONPATH variable
            with open(shFilename, "r") as shFile, open(mingwShFilename, "w+") as mingwShFile:
                for line in shFile:
                    if "PYTHONPATH=" in line:
                        mingwShFile.write('PYTHONPATH=\"{0}\"${{PYTHONPATH+;$PYTHONPATH}}\n'.format(pythonpath))
                    else:
                        mingwShFile.write(line)
