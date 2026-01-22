import os
import subprocess

from sys import argv, platform
from pathlib import Path
from shutil import copy2
from datetime import datetime
from types import SimpleNamespace
from colorama import Fore, Style, init

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

	def flush(self):
		items = self.items.values()
		sorted_items = (
			[i for i in items if i.startswith('+')] +
			[i for i in items if i.startswith('-')]
		)
		self.items = {k+1: i for k,i in enumerate(sorted_items)}

	def __str__(self):
		s = ['']
		l = len(str(len(self.items)))
		for k,i in self.items.items():
			i = decode(i)
			fstr = f" {k:>{l}.0f}. {i.txt}"
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
	timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
	newfile = todofile.with_name(f"{todofile.stem}_{timestamp}{todofile.suffix}")
	copy2(todofile, newfile)
	with open(todofile) as fid:
		todos = fid.readlines()
	return [i.strip() for i in todos]

def save_todofile(tdl):
	with open(todofile, 'w') as fid:
		fid.write('\n'.join(tdl.items.values()))

def main() -> None:

	if len(argv) < 2:
		tdl = ToDoList(load_todofile())
		print(tdl)
	elif argv[1] in '-+x':
		tdl = ToDoList(load_todofile())
		tdl.items[len(tdl.items)+1] = ' '.join(argv[1:])
		tdl.sort()
		print(tdl)
		save_todofile(tdl)
	elif argv[1] == 'flush':
		tdl = ToDoList(load_todofile())
		tdl.flush()
		print(tdl)
		save_todofile(tdl)
	elif argv[1] == 'open':
		if platform == 'win32':
			os.startfile(todofile)
		elif platform == 'darwin':
			subprocess.run(['open', todofile])
		else:
			subprocess.run(['xdg-open', todofile])
	else:
		tdl = ToDoList(load_todofile())
		if (
			(s := argv[1][-1]) in '-+x'
			and
			(k := int(argv[1][:-1])) in tdl.items
		):
			tdl.items[k] = s + tdl.items[k][1:]
			tdl.sort()
			print(tdl)
			save_todofile(tdl)
		else:
			print('Unknown command!')
