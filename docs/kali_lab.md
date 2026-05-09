# Kali Lab

## VM esperada

- Nombre: `kali-lab`
- Virtualizador: VirtualBox
- Red: NAT
- SSH local: `127.0.0.1:2222 -> guest:22`
- Uso: herramientas de laboratorio y pentesting autorizado.

## Comprobaciones seguras

```bash
VBoxManage list vms | grep '"kali-lab"'
VBoxManage list runningvms | grep '"kali-lab"'
VBoxManage showvminfo kali-lab --machinereadable | egrep '^(name=|memory=|cpus=|nic1=|Forwarding|VMState=)'
ssh -o BatchMode=yes -o ConnectTimeout=5 kali-lab 'echo SSH_OK && hostname'
```

## Activar SSH dentro de Kali

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
systemctl status ssh --no-pager
```

## Alias SSH recomendado en Ubuntu

```sshconfig
Host kali-lab
  HostName 127.0.0.1
  Port 2222
  User kali
  IdentityFile ~/.ssh/hermes_kali_lab
  IdentitiesOnly yes
```
