xphon_path=$(pwd)

if !(grep -q ${xphon_path} ~/.bashrc)
then
echo "export PATH=${xphon_path}/xphon/bin:\${PATH}" >> ~/.bashrc
echo "export PYTHONPATH=${xphon_path}:\${PYTHONPATH}" >> ~/.bashrc
else
echo "xphon already found on PATH. Please remove it from .bashrc if you want to change the script location."
fi

chmod +x xphon/bin/xphon
