import os
import re
import subprocess

from sys import argv, platform
from pathlib import Path
from shutil import copy2
from types import SimpleNamespace
from colorama import Fore, Style, init

if len(argv) > 2 and argv[1] == '-f':
	todofile = Path.home() / argv[2]
	argv = argv[:1] + argv[3:]
else:
	todofile = Path.home() / ".cltd"

def decode(x):
	return SimpleNamespace(status = x[0], txt = x[1:].strip())

def encode(x):
	return f"{x.status} {x.txt}"

class ToDoList():

	def __init__(self, items):
		self.items = {k+1: i for k,i in enumerate(items)}
		self.sort()

	def sort(self):
		items = self.items.values()
		sorted_items = (
			[i for i in items if i.startswith('+')] +
			[i for i in items if i.startswith('-')] +
			[i for i in items if i.startswith('x')]
		)
		self.items = {k+1: i for k,i in enumerate(sorted_items)}

	def flush(self, toflush = 'x'):
		items = self.items.values()
		items = [i for i in items if i[0] not in toflush]
		self.items = {k+1: i for k,i in enumerate(items)}

	def print(self):
		s = ['']
		l = len(str(len(self.items)))
		for k,i in self.items.items():
			i = decode(i)
			s.append(f"  {k:>{l}.0f}. {i.txt}")
		print('\n'.join(s))

	def __str__(self):
		s = ['']
		l = len(str(len(self.items)))
		for k,i in self.items.items():
			i = decode(i)
			fstr = f"  {k:>{l}.0f}. {i.txt}"
			if i.status == '-':
				fstr = Style.DIM + fstr + Style.RESET_ALL
			elif i.status == 'x':
				fstr = Style.DIM + '\033[9m' + fstr + '\033[0m' + Style.RESET_ALL
			elif i.status == '+':
				fstr = '\033[1m' + Fore.RED + fstr + Fore.RED + '\033[0m'
			s.append(fstr)
		return '\n'.join(s)

def load_todofile():
	todofile.touch(exist_ok = True)
	with open(todofile) as fid:
		todos = fid.readlines()
	return [i.strip() for i in todos]

def save_todofile(tdl, Nb = 100):
	filenames = [
		todofile.with_name(f"{todofile.stem}-backup-{Nb-N}{todofile.suffix}")
		for N in range(Nb)
	] + [todofile]
	for k in range(Nb):
		try:
			copy2(filenames[k+1], filenames[k])
		except FileNotFoundError:
			pass
	with open(todofile, 'w') as fid:
		fid.write('\n'.join(tdl.items.values()))

def main() -> None:

	if len(argv) < 2:

		tdl = ToDoList(load_todofile())
		print(tdl)

	else:

		if argv[1] == 'add':
			if len(argv) < 3:
				print('Missing task :(')
				exit()
			txt = ' '.join(argv[2:])
			if re.compile(r'[-+x]').match(txt):
				s, txt = txt[0], txt[1:].strip()
			else:
				s = '-'

			tdl = ToDoList(load_todofile())
			for k,v in tdl.items.copy().items():
				tdl.items[k+1] = v
			tdl.items[1] = f'{s} {txt}'

			tdl.sort()
			print(tdl)
			save_todofile(tdl)

		elif argv[1] in ('today', 'now', 'top'):
			tdl = ToDoList(load_todofile())
			tdl.flush('-x')
			tdl.print()

		elif argv[1] == 'flush':
			tdl = ToDoList(load_todofile())
			tdl.flush()
			print(tdl)
			save_todofile(tdl)

		elif argv[1] == 'undo':
			files = sorted(
				todofile.parent.glob(f'{todofile.stem}-backup-*{todofile.suffix}'),
				key = lambda s: int(str(s).split('-')[-1])
			)
			if len(files) == 0:
				print('No backup is available :(')
				exit()

			copy2(files[0], todofile)
			for k in range(len(files)-1):
				copy2(files[k+1], files[k])
			files[-1].unlink()

			tdl = ToDoList(load_todofile())
			print(tdl)

		elif argv[1] == 'open':
			if platform == 'win32':
				os.startfile(todofile)
			elif platform == 'darwin':
				subprocess.run(['open', todofile])
			else:
				subprocess.run(['xdg-open', todofile])

		elif argv[1] == 'vi':
			if platform == 'win32':
				print('Not sure how to call vi on Windows :(')
			else:
				subprocess.run(['vi', todofile])
				tdl = ToDoList(load_todofile())
				print(tdl)


		elif (( # change status of a given task
			p := re.compile(r'(?P<i>\d*)(?P<s>[-+x])$').match(argv[1])
		) or (
			p := re.compile(r'(?P<s>[-+x])(?P<i>\d*)$').match(argv[1])
		)):
			i = int(p.group('i'))
			s = p.group('s')
			tdl = ToDoList(load_todofile())
			if i not in tdl.items:
				print('No task with that index :(')
			else:
				tdl.items[i] = s + tdl.items[i][1:]
				tdl.sort()
				print(tdl)
				save_todofile(tdl)

		elif ( # if first arg is just numbers
			re.compile(r'\d*$').match(argv[1])
		):
			i = int(argv[1])
			tdl = ToDoList(load_todofile())
			if i not in tdl.items:
				print('No task with that index :(')
			else:
				if len(argv) < 3:
					print(f'Missing instruction for task {i} :(')
					exit()
				if argv[2] in ('x', 'done'):
					tdl.items[i] = 'x' + tdl.items[i][1:]
					tdl.sort()
					print(tdl)
					save_todofile(tdl)
				if argv[2] in ('+', 'today', 'now', 'top'):
					tdl.items[i] = '+' + tdl.items[i][1:]
					tdl.sort()
					print(tdl)
					save_todofile(tdl)
				if argv[2] in ('-', 'later'):
					tdl.items[i] = '-' + tdl.items[i][1:]
					tdl.sort()
					print(tdl)
					save_todofile(tdl)

		else:

			print('Unknown command :(')
