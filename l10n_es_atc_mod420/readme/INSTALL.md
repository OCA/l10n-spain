Para instalar este modulo y usar el .jar se necesitan las siguientes librerias: `openjdk-8-jdk`, `ttf-mscorefonts-installer`, y `fontconfig`.

Ejemplo en Debian/Ubuntu

```bash
echo "deb http://deb.debian.org/debian unstable main non-free contrib" > /etc/apt/sources.list
echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections
apt-get update
apt-get install -y --no-install-recommends openjdk-8-jdk ttf-mscorefonts-installer fontconfig
fc-cache -f -v
```