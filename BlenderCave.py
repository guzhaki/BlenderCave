#!/usr/bin/env python3.2
## Copyright © LIMSI-CNRS (2013)
##
## contributor(s) : Jorge Gascon, Damien Touraine, David Poirier-Quinot,
## Laurent Pointal, Julian Adenauer, 
## 
## This software is a computer program whose purpose is to distribute
## blender to render on CAVE(TM) device systems.
## 
## This software is governed by the CeCILL  license under French law and
## abiding by the rules of distribution of free software.  You can  use, 
## modify and/ or redistribute the software under the terms of the CeCILL
## license as circulated by CEA, CNRS and INRIA at the following URL
## "http://www.cecill.info". 
## 
## As a counterpart to the access to the source code and  rights to copy,
## modify and redistribute granted by the license, users are provided only
## with a limited warranty  and the software's author,  the holder of the
## economic rights,  and the successive licensors  have only  limited
## liability. 
## 
## In this respect, the user's attention is drawn to the risks associated
## with loading,  using,  modifying and/or developing or reproducing the
## software by the user in light of its specific status of free software,
## that may mean  that it is complicated to manipulate,  and  that  also
## therefore means  that it is reserved for developers  and  experienced
## professionals having in-depth computer knowledge. Users are therefore
## encouraged to load and test the software's suitability as regards their
## requirements in conditions enabling the security of their systems and/or 
## data to be ensured and,  more generally, to use and operate it in the 
## same conditions as regards security. 
## 
## The fact that you are presently reading this means that you have had
## knowledge of the CeCILL license and that you accept its terms.
## 

import os
import sys
import time
import socket

arguments = {}

if 'BLENDER_CAVE_GLOBAL_CONFIGURATION' not in os.environ:
    print('Invalid global BlenderCave configuration file: you should define BLENDER_CAVE_GLOBAL_CONFIGURATION environment variable to point to the correct conf.py file')
    sys.exit()

exec(open(os.environ['BLENDER_CAVE_GLOBAL_CONFIGURATION']).read())

if len(sys.argv) < 2:
    print("Usage:", sys.argv[0], "[start|startalone|stop|stopalone] file.blend")
    sys.exit()

if sys.argv[1] == 'stop' or sys.argv[1] == 'start':
    arguments['config-file'] = all_config_file
    arguments['background'] = True
else:
    arguments['config-file'] = alone_config_file
    arguments['background'] = False

if (sys.argv[1] == 'version'):
    exec(open(os.path.join(blender_cave_path, 'blender_cave', 'version.py')).read())
    print('BlenderCave version: ', version)
    sys.exit()

sys.path.append(os.path.join(blender_cave_path, 'utils', 'launcher'))

import work_on_blender_cave
controller = work_on_blender_cave.WorkOnBlenderCave(blender_cave_path, arguments['config-file'], arguments['config-path'])

controller.compileBlenderCave()

configuration = controller.getConfiguration()
computers = configuration['computers']

if False:
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(computers)
    sys.exit()

def quoteString(string):
    if ' ' in string:
        return '"' + string + '"'
    return string

if sys.platform == "win32":
    blender_program = "blenderplayer.exe"
else:
    blender_program = "blenderplayer"

if 'blenderplayer_path' in globals():
    arguments['blender_player'] = quoteString(os.path.join(blenderplayer_path, blender_program))
else:
    for path in os.environ["PATH"].split(os.pathsep):
        file = os.path.join(path, blender_program)
        if os.path.isfile(file) and os.access(file, os.X_OK):
            arguments['blender_player'] = quoteString(file)
            break

arguments['pid-path'] = os.path.join(temp_path, 'pid')
arguments['rb-path']  = os.path.join(temp_path, 'rb')

run_script = sys.executable + ' ' + os.path.join(blender_cave_path, 'utils', 'run.py')

arguments['blender_cave_path'] = blender_cave_path

def createCommand(arguments):
    command = [run_script]
    for argument in ({'key' : 'python_path',       'prefix' : '--python-path'       },
                     {'key' : 'blender_player',    'prefix' : '--blender-player'    },
                     {'key' : 'command',           'prefix' : '--command'           },
                     {'key' : 'blender_cave_path', 'prefix' : '--blender-cave-path' },
                     {'key' : 'pid-path',          'prefix' : '--pid-path'          },
                     {'key' : 'screen',            'prefix' : '--screen'            },
                     {'key' : 'options',           'prefix' : '--options'           },
                     {'key' : 'blender-file',      'prefix' : '--blender-file'      },
                     {'key' : 'config-file',       'prefix' : '--config-file'       },
                     {'key' : 'config-path',       'prefix' : '--config-path'       },
                     {'key' : 'log-path',          'prefix' : '--log-path'          },
                     {'key' : 'verbosity',         'prefix' : '--verbosity'         },
                     {'key' : 'display',           'prefix' : '--display'           },
                     {'key' : 'rb-path',           'prefix' : '--rb-path'           }):

        if argument['key'] in arguments:
            command.append(argument['prefix'] + "=" + arguments[argument['key']])

    for argument in ({'key' : 'clear_previous', 'argument' : '-c' },
                     {'key' : 'background',     'argument' : '-b' }):
        if arguments[argument['key']]:
            command.append(argument['argument'])

    return ' '.join(command)

def runCommand(computer, command):
    if computer != 'localhost' and computer != socket.gethostname():
        command = command.replace('"', '\\"')
        if sys.platform == "win32":
            user     = windows_logins[computer]['user']
            password = windows_logins[computer]['password']
            command  = 'start psexec \\' + '\\' + computer + ' -u ' + user + ' -p ' + password + ' -i ' + command
        else:
            command = 'ssh ' + computer + ' "' + command + '"'
    #print('run : ', command)
    os.system(command)

class InvalidCall(Exception):
    pass

try:

    if (sys.argv[1] == 'start') or (sys.argv[1] == 'startalone'):
        arguments['command'] = 'start'
    elif (sys.argv[1] == 'stop') or (sys.argv[1] == 'stopalone'):
        arguments['command'] = 'stop'
    else:
        raise InvalidCall

    try:
        blend_file = sys.argv[2]
        if not os.path.isabs(blend_file):
            blend_file = quoteString(os.path.join(os.getcwd(), blend_file))
        controller.compileBlenderFileModule(blend_file)
        arguments['blender-file'] = blend_file
    except IndexError:
        if arguments['command'] == 'start':
            raise

    instances           = {}
    for computer, screens in computers.items():
        instances[computer] = []
        for screen, attributs in screens.items():
            screen_arguments                = arguments
            screen_arguments['screen']      = screen
            if 'player' in attributs:
                if 'display' in attributs['player']:
                    screen_arguments['display'] = attributs['player']['display']
                if 'options' in attributs['player']:
                    screen_arguments['options'] = quoteString(attributs['player']['options'])
            command = createCommand(screen_arguments)
            
            if attributs['master']:
                master_computer = computer
                master_command  = command
            else:
                instances[computer].append(command)

    for computer, commands in instances.items():
        for command in commands:
            runCommand(computer, command)
    time.sleep(1)
    runCommand(master_computer, master_command)

except InvalidCall:
    print('usage : ', sys.argv[0], ' [start file.blend]|stop')
