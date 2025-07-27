#!/usr/bin/expect

spawn /tmp/client.run --accept --nox11 --target /tmp/expressvpn --keep
expect {
    -re "Continue installing .*$" { send "y\r" }
}
# expect eof
