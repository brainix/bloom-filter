#-----------------------------------------------------------------------------#
#   Makefile                                                                  #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



venv ?= venv

init upgrade: formulae := {openssl,readline,xz,pyenv,memcached}

python: version ?= 2.7.14



install: init python

init:
	-xcode-select --install
	command -v brew >/dev/null 2>&1 || \
		ruby -e "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
	brew analytics off
	brew analytics regenerate-uuid
	brew install $(formulae)

python:
	CFLAGS="-I$(shell brew --prefix openssl)/include -I$(shell brew --prefix readline)/include -g -O2" \
		LDFLAGS="-L$(shell brew --prefix openssl)/lib -L$(shell brew --prefix readline)/lib" \
		pyenv install --skip-existing $(version)
	pyenv rehash
	rm -rf $(venv)
	~/.pyenv/versions/$(version)/bin/pip install virtualenv
	~/.pyenv/versions/$(version)/bin/virtualenv $(venv)
	source $(venv)/bin/activate && \
		pip install --upgrade pip virtualenv && \
		pip install --requirement requirements.txt

upgrade:
	brew update
	-brew upgrade $(formulae)
	brew cleanup
	pyenv rehash
	source $(venv)/bin/activate && \
		pip install --upgrade pip virtualenv && \
		pip install --requirement requirements-to-freeze.txt --upgrade && \
		pip freeze > requirements.txt
	git status
	git diff

clean:
	rm -rf {$(venv),.coverage}

services:
	/usr/local/opt/memcached/bin/memcached

test:
ifeq ($(tests),)
	source $(venv)/bin/activate && \
		coverage run -m unittest discover --start-directory tests --verbose && \
		coverage report && \
		pyflakes bloom/*\.py tests/*\.py
else
	source $(venv)/bin/activate && \
		python -m unittest --verbose $(tests)
endif
