
import sublime
import sublime_plugin
import os
import sys
import subprocess
import functools
import time

import _thread
import re
import string


class ProcessListener(object):

    def on_data(self, proc, data, is_err):
        pass

    def on_finished(self, proc):
        pass

# Encapsulates subprocess.Popen, forwarding stdout to a supplied
# ProcessListener (on a separate thread)


class AsyncProcess(object):

    def __init__(self, arg_list, env, listener, encoding,
                 # "path" is an option in build systems
                 path="",
                 # "shell" is an options in build systems
                 shell=False,):

        self.listener = listener
        self.encoding = encoding
        self.killed = False

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Set temporary PATH to locate executable in arg_list
        if path:
            old_path = os.environ["PATH"]
            # The user decides in the build system whether he wants to append $PATH
            # or tuck it at the front: "$PATH;C:\\new\\path",
            # "C:\\new\\path;$PATH"
            os.environ["PATH"] = os.path.expandvars(
                path).encode(sys.getfilesystemencoding())

        proc_env = os.environ.copy()
        proc_env.update(env)       

        for k, v in proc_env.items():
            proc_env[k] = os.path.expandvars(
                v).encode(sys.getfilesystemencoding())

        self.proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=shell)

        if path:
            os.environ["PATH"] = old_path

        if self.proc.stdout:
            _thread.start_new_thread(self.read_stdout, ())

        if self.proc.stderr:
            _thread.start_new_thread(self.read_stderr, ())

    def kill(self):
        if not self.killed:
            self.killed = True
            self.proc.terminate()
            self.listener = None

    def poll(self):
        return self.proc.poll() == None

    def exit_code(self):
        return self.proc.poll()

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2**15)
            data = data.decode(self.encoding)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data, False)
            else:
                self.proc.stdout.close()
                if self.listener:
                    self.listener.on_finished(self)
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2**15)
            data = data.decode(self.encoding)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data, True)
            else:
                self.proc.stderr.close()
                break


class CatkinBuildCommand(sublime_plugin.WindowCommand, ProcessListener):

    def setup(self, kill, env):

        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
                return

        #if already running kill and start again
        if hasattr(self, 'proc'):
            self.proc.kill()
            self.proc = None

        # Setup output window
        self.output_view = self.window.get_output_panel("exec")
        self.output_view.set_syntax_file("Catkin.tmLanguage")
        self.output_view.settings().set("auto_indent", False)

        # Default the to the current files directory if no working directory
        # was given
        if (self.working_dir == "" and self.window.active_view() and self.window.active_view().file_name()):
            self.working_dir = os.path.dirname(
                self.window.active_view().file_name())

        # Setup parameters
        self.proc = None
        self.out_msg = ''
        self.err_msg = ''
        self.keep_data = False
        self.keep_output = False
        self.clear_line = False

        # Call get_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.get_output_panel("exec")

        show_panel_on_build = sublime.load_settings(
            "Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

        self.merged_env = env.copy()
        if self.window.active_view():
            user_env = self.window.active_view().settings().get('build_env')
            if user_env:
                self.merged_env.update(user_env)

        # Change to the working dir, rather than spawning the process with it,
        # so that emitted working dir relative path names make sense
        if self.working_dir != "":
            os.chdir(self.working_dir)

    def genBuildCommand(self):

        # create build command
        if self.run_tests:
            build_command = ['catkin','run_tests','--this']
        else:
            build_command = ['catkin','build','--this']

        if self.settings.get('color'):
            build_command.append('--force-color')
        else:
            build_command.append('--no-color')

        if self.build_deps is False:
            build_command.append('--no-deps')

        if self.settings.get('status-updates') is False:
            build_command.append('--no-status')

        if self.debug:
            build_command.append('--cmake-args -DCMAKE_BUILD_TYPE=Debug')

        return build_command

    def run(self, working_dir="", build_deps=False, run_tests=False, debug=False, env={}, encoding='utf-8', kill=False, **kwargs):

        # set inputs
        self.working_dir = working_dir
        self.build_deps = build_deps
        self.run_tests = run_tests
        self.debug = debug
        self.encoding = encoding

        #load in settings
        self.settings = sublime.load_settings("CatkinBuild.sublime-settings")

        self.setup(kill, env)

        build_command = self.genBuildCommand()      
       
        # run build        
        self.run_async(build_command)

    def run_async(self, cmd):

        err_type = OSError
        if os.name == "nt":
            err_type = WindowsError

        try:
            # Forward kwargs to AsyncProcess
            self.proc = AsyncProcess(cmd, self.merged_env, self, self.encoding)
        except err_type as e:
            self.output_text(None, str(e) + "\n")
            self.output_text(None, "[cmd:  " + str(cmd) + "]\n")
            self.output_text(None, "[dir:  " + str(os.getcwdu()) + "]\n")
            if "PATH" in self.merged_env:
                self.output_text(
                    None, "[path: " + str(self.merged_env["PATH"]) + "]\n")
            else:
                self.output_text(
                    None, "[path: " + str(os.environ["PATH"]) + "]\n")

    def is_enabled(self, kill=False):
        if kill:
            return hasattr(self, 'proc') and self.proc and self.proc.poll()
        else:
            return True

    def finish(self, proc):

        # check for issues
        if len(self.err_msg) is not 0:
            print(self.err_msg)
            self.output_text(proc, self.err_msg)

        # find first error
        output_err, err_free = self.firstErr(self.out_msg)

        if(err_free):
            self.output_text(proc, '\nSUCCESSFUL BUILD')
        else:
            if self.settings.get("repeat-error"):
                self.output_text(proc, output_err)
            self.output_text(proc, '\nFAILED BUILD')

    def on_data(self, proc, data, is_err):
        sublime.set_timeout(functools.partial(
            self.process_data, proc, data, is_err), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)

    def process_data(self, proc, data, is_err):

        # check error data 
        if is_err:
            self.err_msg += data

        # check message data
        else:
            # need to delete last line
            if self.clear_line:
                self.clear_line = False

                self.output_view.run_command("left_delete")
                self.output_view.run_command(
                    "expand_selection", {"to": "line"})
                self.output_view.run_command("left_delete")

            # remove junk from output
            trimmed = self.trimOutput(data)
            if self.settings.get("trim-output"):
                data = trimmed
            # replace question marks
            if self.settings.get("replace-q"):
                data = data.replace('?', '\'')

            self.output_text(proc, data)
            self.out_msg += data

            #if build line delete it so things keep updating
            if '[build' in data:
                self.clear_line = True

    def output_text(self, proc, text):

        if proc != self.proc:
            # a second call to exec has been made before the first one
            # finished, ignore it instead of intermingling the output.
            if proc:
                proc.kill()
            return

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Ignore warning about terminal width
        if not "NOTICE: Could not determine the width of the terminal." in text:
            self.output_view.run_command("insert", {"characters": text})

    def trimOutput(self, str_in):
        if self.settings.get("color"):
            start_flag = 'Starting  [1m[32m>>>[0m '
            finished_flag = '[1m[30mFinished[0m  [32m<<<[0m '
            failed_flag = '[1m[31mFailed[0m    [31m<<<[0m '
        else:
            start_flag = 'Starting >>> '
            finished_flag = 'Finished <<< '
            failed_flag = 'Failed <<< '

        str_out = ''
        for line in str_in.splitlines():
            if start_flag in line:
                self.keep_data = True

            if self.keep_data:
                str_out += line + '\n'

            if (finished_flag in line) or (failed_flag in line):
                self.keep_data = False

        return str_out

    def firstErr(self, str_in):
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

        # remove last enter
        err_str = err_str[:-1]

        return(err_str, err_free)
