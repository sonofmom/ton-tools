#!/bin/sh
# This script will generate JSON liteserver structure for local configuration file.
#
# Required params:
# HEX representation of LITESERVER key
# Liteserver server port
#
# Example: mklite.sh F20F63AFEF12926D0B0A023C8AA8217BDFF731E60EEE236D3D21C535E7F88F9C 6501
#

hex2base()
{
  echo $1  | xxd -r -p | openssl base64
}

echo "\"liteservers\" : [
  { 
    \"id\" : \""$(hex2base $1)"\",
    \"port\" : $2
  }
],"

