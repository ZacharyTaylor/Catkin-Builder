import argparse
import subprocess
import sys
import re
import string

def getArgs():
  parser = argparse.ArgumentParser(description='Wrapper for catkin build to simplify build process.')
  parser.add_argument('-p', '--path', help='path to ros package to build. May be a subdirectory or file path.')
  parser.add_argument('-d', '--build_deps', type=bool, help='(Optional bool, default = false). Controls if the dependencies of the package are also be built')
  parser.add_argument('-c', '--color', type=bool, help='(Optional bool, default = false). Controls if the output retains text color')
  parser.add_argument('-s', '--keep_status', type=bool, help='(Optional bool, default = false). Controls if the output status is retained (will not be printed until build completes)')
  parser.add_argument('-t', '--trim_output', type=bool, help='(Optional bool, default = true). Controls if the build message is trimmed to remove everything not critical to the build')
  parser.add_argument('-q', '--remove_q', type=bool, help='(Optional bool, default = true). Controls removal of question marks form output (work around for issue where catkin returns ? where text should be bold)')
  parser.add_argument('-r', '--repeat_err', type=bool, help='(Optional bool, default = true). Controls if the first error encountered is repeated at the end of the build')

  args = parser.parse_args()

  #Set default values where needed
  if args.build_deps is None:
    args.build_deps = False
  if args.color is None:
    args.color = False
  if args.keep_status is None:
    args.keep_status = False
  if args.repeat_err is None:
    args.repeat_err = True
  if args.trim_output is None:
    args.trim_output = True
  if args.remove_q is None:
    args.remove_q = True

  return args

def trimOutput(str_in, color_flag):
  if color_flag:
    start_flag = 'Starting  [1m[32m>>>[0m '
    finished_flag = '[1m[30mFinished[0m  [32m<<<[0m '
    failed_flag = '[1m[31mFailed[0m    [31m<<<[0m '
  else:
    start_flag = 'Starting >>> '
    finished_flag = 'Finished <<< '
    failed_flag = 'Failed <<< '

  str_out = ''
  keep = False
  for line in str_in.splitlines():
    if start_flag in line:
      keep = True

    if keep:
      str_out += line + '\n'

    if (finished_flag in line) or (failed_flag in line):
      keep = False

  return str_out

def firstErr(str_in):
  error_flag = 'error: '
  linker_flag = 'undefined reference to '
  note_flag = 'note: '
  include_flag = 'In file included from '
  end_flag = 'Error 1'

  err_str = '\nErrors encountered, reprinting first error:\n...............................................................................\n'
  err_free = True
  keep = False

  for line in str_in.splitlines():
    if err_free and ((error_flag in line) or (linker_flag in line)):
      keep = True
      err_free = False
    elif any(s in line for s in (error_flag, linker_flag, note_flag, include_flag, end_flag)): 
      keep = False

    if keep:
      err_str += line + '\n'

  #remove last enter
  err_str = err_str[:-1]

  return(err_str, err_free)

args = getArgs()

#get package name
output,error = subprocess.Popen(['catkin', 'list', '--this'], stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()

#check for issues
if len(error) is not 0:
  print(error)
  exit()
if len(output) is 0:
  print('Could not find any package in ' + args.path + ' to build, exiting')
  exit()

#grab package name
catkin_package = output[2:-1]
print('Building ' + catkin_package + '...')
sys.stdout.flush()

#create build command
build_command = ['catkin', 'build', catkin_package]

if args.color:
  build_command.append('--force-color')
else:
  build_command.append('--no-color')

if args.build_deps is False:
  build_command.append('--no-deps')

if args.keep_status is False:
  build_command.append('--no-status')

#run build
output,error = subprocess.Popen(build_command, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()

#remove question marks
if args.remove_q:
  output = output.replace('?','')

#remove junk from output
if args.trim_output:
  output = trimOutput(output, args.color)

#find first error
output_err, err_free = firstErr(output)

#print output
print(output)

if(err_free):
  print('SUCCESSFUL BUILD')
else:
  if(args.repeat_err):
    print(output_err)
  print('FAILED BUILD')