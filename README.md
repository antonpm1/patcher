# patcher
The aim of this project is to provide a script that will patch a RHEL/Centos/OEL server using the Spacewalk API with the following journey:

1. Assess if the server is online according to Spacewalk
2. Apply waiting updates and track the success/failure
3. Reboot if kernel update is applied
4. Ensure server returns (is online according to Spacewalk)

Run with the following:

./upgrade fqdn_of_server

api-user is set up in Spacewalk and has admin access
Enter password for api-user (or hard-code into script)
