#!/usr/bin/env python2.7
# -*- encoding: utf-8 -*-

import os, zipfile, getpass, hashlib, io, shutil
from Crypto.Cipher import AES

BS = 16	# Using AES-128bit because I tried 256bit and everything fell apart.
# Both of the lambda functions below are copy-pasted from here: https://goo.gl/Uc9t2k
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode()	# Chinese to me
unpad = lambda s: s[:-ord(s[len(s)-1:])]	# Chinese to me

KEY = False
# And you might ask: but, JlXip, why are you storing the key in memory instead of the cipher instance?
# And I might answer: a wizard did it.
# I don't know why using twice the cipher instance breaks everything. I really don't know.
# If you are reading this and you know why, please tell me.

def stage2():
	if KEY == False: setKey()	# If key is not set (if a brand new safe box is being created), set it.

	# Zip the files
	SAFEBOX = False
	TMP = False
	try:
		SAFEBOX = io.BytesIO()	# Create an empty file in memory
		TMP = zipfile.ZipFile(SAFEBOX, 'w')	# Create a new zip in that file
	except:
		print 'Error creating the zip file.'
		exit()
	try:
		for root, dirs, files in os.walk(WORKING_DIRECTORY):	# Walking around
			for file in files:
				path = os.path.join(root, file)	# The absolute path (in the system)
				rel_path = path[len(WORKING_DIRECTORY) :]	# The relative path (in the zip)
				TMP.write(path, rel_path)	# Add to the zip

				# Shred the file
				with open(os.path.join(root, file), 'ab') as f:	# Open file in write mode
					f.seek(0, 2)	# Go to the end of the file
					s = f.tell()	# Store the size
					f.seek(0)	# Go back to the beginning of the file
					f.write(chr(0)*s)	# Overwrite
	except:
		print 'Error reading files in disk.'
		exit()

	TMP.close()	# Close the zip
	TMP = False	# Remove form memory

	shutil.rmtree(WORKING_DIRECTORY)	# Remove the shredded files.

	C = setC()	# Get a cipher instance.

	# Encrypt
	try:
		SAFEBOX = C.encrypt(pad(SAFEBOX.getvalue()))	# Get the binary data, pad it, and encrypt it.
	except:
		print 'Error encrypting the safe box.'
		exit()

	# Write safe box
	with open(ENC, 'wb') as f:
		f.write(SAFEBOX)

	SAFEBOX = False	# Remove from memory
	return

def stage1():
	# Read safe box
	SAFEBOX = False
	try:
		with open(ENC, 'rb') as f:
			SAFEBOX = f.read()	# Read bytes from the encrypted safe box.
	except:
		print 'The \'SafeBox.ENC\' file doesn\'t exist.'
		exit()

	setKey()	# Ask for the key, as KEY == False is true for all executions.
	C = setC()	# Get a cipher instance.

	# Decrypt
	try:
		SAFEBOX = unpad(C.decrypt(SAFEBOX))	# Decrypt and then unpad.
	except:
		print 'Incorrect password or the safe box is corrupt.'
		exit()

	# Load zip
	try:
		SAFEBOX = zipfile.ZipFile(io.BytesIO(SAFEBOX))	# Create a file from the decrypted bytes and open that as a zip.
	except:
		print 'The decoded file isn\'t a valid safe box.'
		exit()

	# Unzip
	os.makedirs(WORKING_DIRECTORY)	# Create the directory
	SAFEBOX.extractall(WORKING_DIRECTORY)	# Extract the zip into the directory
	SAFEBOX.close()	# Close the zip
	SAFEBOX = False	# Remove from memory

	os.remove(ENC)	# Remove encrypted file. Which is not necessary anymore. No need to shred.
	return

def setC():	# Create cipher
	try:
		return AES.new(KEY, AES.MODE_CBC, chr(0)*BS)	# New AES instance, CBC mode, null IV.
	except:
		print 'Error creating cipher.'
		exit()

def setKey():	# Ask for the key
	# The key will be hashed in SHA-256 in order to get an easy-to-work-with key size.
	global KEY
	KEY = hashlib.sha256(getpass.getpass()).digest()

p = os.getcwd()	# Current directory
WORKING_DIRECTORY = os.path.join(p, 'SafeBox') + os.sep	# The directory the decrypted files will be stored
ENC = os.path.join(p, 'SafeBox.ENC')	# The encrypted safe box.

if __name__ == '__main__':
	# If the directory already exists, warn the user.
	if os.path.isdir(WORKING_DIRECTORY):
		print 'WARNING\n'
		print 'The directory \'SafeBox\' already exists.\n'

		if(raw_input('Are you trying to create a BRAND NEW safe box? [y/N]: ').upper() == 'Y'):
			stage2()	# Run ONLY stage 2, as we want to create a new safe box.
			print 'Safe box created.'
		else:
			print 'Please, backup what necessary and remove that directory.'
		exit()

	stage1()	# Run stage 1
	print '\nYour files are now available.'
	raw_input('Hit [RETURN] when you are finished.')

	stage2()	# Run stage 2
	print '\nAll clean.'