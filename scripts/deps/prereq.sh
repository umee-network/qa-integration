#/bin/bash

## This script installs the basic apt packages and also checks if go is installed on the system or
## not. If go is not installed on the system then go1.17.3 is installed by the script. Env variables
## related to go are also exported to bashrc.

command_exists () {
  type "$1" &> /dev/null ;
}

is_macos() {
  [[ "$OSTYPE" == "darwin"* ]]
}

install_macos() {
  if command_exists brew; then
    brew install $1
  else
    echo 'Please install `brew` and try again, eg:'
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
  fi
}

install_go () {
  sudo rm -rf /usr/local/go
  echo "Install dependencies"
  sudo apt update
  sudo apt install build-essential jq -y
  wget -q https://dl.google.com/go/go$goversion.linux-amd64.tar.gz
  tar -xf go$goversion.linux-amd64.tar.gz
  sudo cp -R go /usr/local
  go_path=`which go`
  if [ ! -z "$go_path" ]; then
    sudo cp go/bin/go $go_path
  fi
  rm -rf go$goversion.linux-amd64.tar.gz go
  export GOPATH=$HOME/go
  echo "" >> ~/.bashrc
  echo 'export GOROOT=/usr/local/go' >> ~/.bashrc
  source ~/.bashrc
}

# get absolute parent directory path of current file
CURPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $CURPATH
source ../../env-umee

if command_exists go;
then
  echo "Golang is already installed"
  echo "checking go version"
  goversionstr="$(go version)"
  if [[ ! "$goversionstr" == *"$goversion"* ]]
  then
    echo "$goversionstr is different of $goversion"
    if is_macos; then
      install_macos golang
    else
      install_go
    fi
  else
    echo "It is the same version, will not install"
  fi
else
  install_go
fi

which go
go version

if command_exists python3 ; then
  echo "python3-dev is already installed"
else
  echo "Installing python3-dev"
  if is_macos ; then
    install_macos python3
  else
    sudo apt update
    sudo apt install python3-dev -y
  fi
fi

if command_exists pylint ; then
  echo "pylint is already installed"
else
  echo "Installing pylint"
  if is_macos ; then
    install_macos pylint
  else
    sudo apt update
    sudo apt install pylint -y
  fi
fi

if is_macos ; then
  # pip3 is installed with brew, above
  pip3 install -r ../../internal/requirements.txt
else
  if ! command_exists pip ; then
    echo "Installing pip"
    sudo apt update
    sudo apt install python3-pip -y
  fi
  pip install -r ../../internal/requirements.txt
fi

if command_exists mongod ; then
  echo "mongo db is already installed"
else
  echo "Installing mongo db"
  if is_macos ; then
    brew tap mongodb/brew
    brew update
    install_macos mongodb-community@6.0
  else
    sudo apt-get install gnupg
    wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
    sudo apt-get update -y
    sudo apt-get install mongodb-org -y
  fi
fi

if is_macos ; then
  brew services start mongodb-community@6.0
else
  # TODO: check how to do that without systemctl
  if command_exists systemctl ; then
    sudo systemctl start mongod
  fi
fi
