#!/usr/bin/python3
# --------------------------------------------------------------------------------------------------
#
#     Nom : backup_avaya.py
#  Auteur : Allard Chris
#    Date : 18/08/2016
# Version : 1.1
#  Github : https://github.com/Allard-Chris/avaya-switches-backup-script-TFTP-version-.git
#
# This script connect to a list of Avaya switches for initiating a backup command to a TFTP server.
# It use Telnet protocol and the login should be the same all on switches that the script will go.
# It require an TFTP server where the backups will be saved.
#
# --------------------------------------------------------------------------------------------------

# Import library
from datetime import datetime
import getpass
import re
import signal
import socket
import sys
import telnetlib
import time

# Function to stop the program
def close_program(signal, frame):
    print("End of script")
    sys.exit(0)


# Function checking IP address syntax
def is_valid_ip(ip):
    result = re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip)
    return bool(result)


# Call function when system want to stop (command ctrl+c)
signal.signal(signal.SIGINT, close_program)

# VARIABLE SET
tftp_server = "192.168.1.20"  # tftp server where will be sent backups
timeout = 120  # Waiting time before considering that there is a timeout (in seconds)
log_file = "log.txt"  # Name of output file
hosts_file = "hosts.txt"  # Name of input file where they are IP address of switches
telnet_port = 23  # Default telnet port

# Account Parameters
user = input("Enter your remote account: ")  # Variable for user account
password = getpass.getpass()  # Variable for password account

# Other Variable
successful = 0
failure = 0

# Create an output file for the results
log = open(log_file, "w")  # Open or create the file in writing mode

# Load input file
try:
    input_file = open(hosts_file, "r")  # Open file in read mode
    hosts = input_file.readlines()
    input_file.close()
except IOError:
    print("Error opening file")
    sys.exit(0)

# Loop on all lines in input file
for ip_address in hosts:
    ip_address = ip_address[: len(ip_address) - 1]  # Delete carriage return line feed
    # Obvious...
    if is_valid_ip(ip_address):
        try:
            telnet = telnetlib.Telnet(
                ip_address, telnet_port, timeout
            )  # Open terminal socket to host

            print(
                time.strftime("%d/%m/%y %H:%M:%S", time.localtime())
                + " Running on : "
                + ip_address
            )  # For user information

            # The various commands to authenticate to the Avaya's switches
            telnet.read_until(
                "***************************************************************",
                timeout,
            )  # Session indicator for Avaya's switches
            telnet.read_until(
                "***************************************************************",
                timeout,
            )  # Session indicator for Avaya's switches (It takes two to indicate when we can enter the accounts)
            telnet.write(
                "\x19" + "\n"
            )  # Order to simulate keybord Ctrl+Y, go to see => http://donsnotes.com/tech/charsets/ascii.html
            telnet.write("\t")  # Order to simulate tabulation key
            telnet.write(user + "\n")  # Enter username
            telnet.write(password + "\n")  # Enter password
            telnet.write("\x63" + "\n")  # Get through the menu after logon for ESR

            # Function to retrieve the name of the switch
            host_name = telnet.read_until("#", timeout)
            for iteration, letter in enumerate(reversed(host_name)):
                if letter == "\n":
                    host_name = host_name[
                        (len(host_name) - iteration) : (len(host_name) - 1)
                    ]
                    break

            telnet.write(
                "copy running-config tftp address "
                + tftp_server
                + " filename "
                + ip_address
                + "-"
                + host_name
                + "_"
                + datetime.now().strftime("%d/%m/%Y")
                + "\n"
            )  # Switch command for saving configuration in tftp
            telnet.read_until(
                "ACG configuration generation completed", timeout
            )  # Backup successful indication
            telnet.write("exit" + "\n")  # logout from cli to menu for ESR
            telnet.write("\x6C" + "\n")  # logout session
            telnet.close()  # End of telnet session on the host

            # Write for log file
            log.write(
                time.strftime("%d/%m/%y %H:%M:%S", time.localtime())
                + " "
                + ip_address
                + " "
                + host_name
                + " : Successful"
                + "\n"
            )
            print(
                time.strftime("%d/%m/%y %H:%M:%S", time.localtime()) + " Successful"
            )  # For user information
            successful += 1

        except socket.error as error:
            log.write(
                time.strftime("%d/%m/%y %H:%M:%S", time.localtime())
                + " "
                + ip_address
                + " Failure - "
                + str(error)
                + "\n"
            )
            print(
                time.strftime("%d/%m/%y %H:%M:%S", time.localtime())
                + " Failure on : "
                + ip_address
            )  # For user information
            failure += 1

# End of script
print("End of script")
log.write("\n")
log.write(
    time.strftime("%d/%m/%y %H:%M:%S", time.localtime()) + " : End of script" + "\n"
)
log.write("Number of Failures : " + str(failure) + "\n")
log.write("Number of Successful : " + str(successful) + "\n")
sys.exit(0)
