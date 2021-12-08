#!/bin/sh
# This script will generate control record for TON Node.
#
# Required params:
# HEX representation of SERVER key
# HEX representation of CLIENT key
# Control Server port
#
# Example: mkcontrol.sh F20F63AFEF12926D0B0A023C8AA8217BDFF731E60EEE236D3D21C535E7F88F9C 554B3D527868290A78463A1F8AA7B13E3242B509EF844048D8C6102C248A6E78 22009
#

hex2base()
{
  echo $1  | xxd -r -p | openssl base64
}

echo "\"control\" : [
  { \"id\" : \""$(hex2base $1)"\",
    \"port\" : $3,
    \"allowed\" : [
      { \"id\" : \""$(hex2base $2)"\",
        \"permissions\" : 15
      }
    ]
  }
],"

