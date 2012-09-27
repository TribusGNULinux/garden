#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, gtk, webkit, sys

from canaimainstalador.clases.particiones import Particiones
from canaimainstalador.clases.common import UserMessage, ProcessGenerator, \
    reconfigurar_paquetes, desinstalar_paquetes, instalar_paquetes, lista_cdroms, \
    crear_etc_default_keyboard, crear_etc_hostname, crear_etc_hosts, \
    crear_etc_network_interfaces, assisted_mount, preseed_debconf_values
from canaimainstalador.config import INSTALL_SLIDES

class PasoInstalacion(gtk.Fixed):
    def __init__(self, CFG):
        gtk.Fixed.__init__(self)
        self.p = Particiones()
        self.w = CFG['wizard']
        self.metodo = CFG['metodo']
        self.acciones = CFG['acciones']
        self.teclado = CFG['teclado']
        self.passroot = CFG['passroot']
        self.nombre = CFG['nombre']
        self.usuario = CFG['usuario']
        self.passuser = CFG['passuser']
        self.maquina = CFG['maquina']
        self.oem = CFG['oem']
        self.chkgdm = CFG['chkgdm']
        self.mountpoint = '/target'
        self.squashfs = '/live/image/live/filesystem.squashfs'
        self.connection = True
        self.requesturl = 'http://www.google.com/'
        self.uninstpkgs = ['canaima-instalador']
        self.reconfpkgs = [
            'cunaguaro', 'guacharo', 'canaima-estilo-visual', 'canaima-plymouth',
            'canaima-chat-gnome', 'canaima-bienvenido-gnome', 'canaima-escritorio-gnome',
            'canaima-base'
            ]
        self.instpkgs_burg = [
            ['/live/image/pool/main/libx/libx86', 'libx86-1']
            ['/live/image/pool/main/s/svgalib', 'libsvga1']
            ['/live/image/pool/main/libs/libsdl1.2', 'libsdl1.2']
            ['/live/image/pool/main/g/gettext', 'gettext-base']
            ['/live/image/pool/main/b/burg-themes', 'burg-themes-common']
            ['/live/image/pool/main/b/burg-themes', 'burg-themes']
            ['/live/image/pool/main/b/burg', 'burg-common']
            ['/live/image/pool/main/b/burg', 'burg-emu']
            ['/live/image/pool/main/b/burg', 'burg-pc']
            ['/live/image/pool/main/b/burg', 'burg']
            ]
        self.instpkgs_cpp = [[
            '/live/image/pool/main/c/canaima-primeros-pasos/',
            'canaima-primeros-pasos'
            ]]
        self.instpkgs_cagg = [[
            '/live/image/pool/main/c/canaima-accesibilidad-gdm-gnome/',
            'canaima-accesibilidad-gdm-gnome'
            ]]
        self.debconflist = [
            'burg-pc burg/linux_cmdline string quiet splash',
            'burg-pc burg/linux_cmdline_default string quiet splash vga=791',
            'burg-pc burg-pc/install_devices multiselect {0}'.format(self.metodo['disco'][0])
            ]
        self.bindlist = [
            ['/dev', self.mountpoint+'/dev', ''],
            ['/dev/pts', self.mountpoint+'/dev/pts', ''],
            ['/sys', self.mountpoint+'/sys', ''],
            ['/proc', self.mountpoint+'/proc', '']
            ]
        self.mountlist = []

        self.visor = webkit.WebView()
        self.visor.set_size_request(700, 400)
        self.visor.open(INSTALL_SLIDES)
        self.put(self.visor, 0, 0)

        msg = 'Ha culminado la instalación, puede reiniciar ahora el sistema o seguir probando canaima y reiniciar más tarde.'
        self.lblInfo = gtk.Label(msg)
        self.lblInfo.set_size_request(690, 280)
        self.put(self.lblInfo, 0, 0)

        self.lblDesc = gtk.Label()
        self.lblDesc.set_size_request(700, 30)
        self.put(self.lblDesc, 0, 290)

        self.w.siguiente.set_label('Reiniciar más tarde')
        self.w.siguiente.set_size_request(150, 30)

        self.w.anterior.set_label('Reiniciar ahora')
        self.w.anterior.set_size_request(150, 30)

        self.w.anterior.hide()
        self.w.siguiente.hide()
        self.w.cancelar.hide()

        self.thread = threading.Thread(target=self.instalar, args=())
        self.thread.start()

    def instalar(self):
        try:
            response = urllib2.urlopen(HeadRequest(self.requesturl))
        except:
            self.connection = False

        self.lblDesc.set_text('Creando particiones en disco ...')
        for a in self.acciones:
            accion = a[0]
            particion = a[1]
            montaje = a[2]
            inicio = a[3]
            fin = a[4]
            fs = a[5]
            tipo = a[6]
            nuevo_fin = a[7]

            self.particiones = self.p.lista_particiones(self.metodo['disco'][0])
            self.cdroms = lista_cdroms()
            particion = self.p.nombre_particion(inicio, fin)

            if accion == 'crear':
                if not self.p.crear_particion(
                    drive=self.metodo['disco'][0], start=inicio,
                    end=fin, fs=fs, partype=tipo
                    ):
                    UserMessage(
                        message='Ocurrió un error creando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
                    )

                    self.mountlist.append([
                        self.p.nombre_particion(inicio, fin),
                        montaje, fs
                        ])

            elif accion == 'borrar':
                if not self.p.borrar_particion(
                    particion=particion
                    ):
                    UserMessage(
                        message='Ocurrió un error borrando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
                    )

            elif accion == 'redimensionar':
                if not self.p.redimensionar_particion(
                    part=particion, newend=nuevo_fin
                    ):
                    UserMessage(
                        message='Ocurrió un error redimensionando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
                    )

            elif accion == 'formatear':
                if not self.p.formatear_particion(
                    part=particion, fs=fs
                    ):
                    UserMessage(
                        message='Ocurrió un error formateando una partición.',
                        title='ERROR',
                        mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                        c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
                    )

            elif accion == 'usar':
                self.mountlist.append([
                    self.p.nombre_particion(inicio, fin),
                    montaje, fs
                    ])

        self.lblDesc.set_text('Montando sistemas de archivos ...')
        assisted_mount(bind=False, plist=self.mountlist)

        self.lblDesc.set_text('Copiando archivos en disco ...')
        if not ProcessGenerator(
            'unsquashfs -f -i -d {0} {1}'.format(self.mountpoint, self.squashfs)
            ):
            UserMessage(
                message='Ocurrió un error copiando los archivos al disco.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
            )

        self.lblDesc.set_text('Montando sistema de archivos ...')
        assisted_mount(bind=True, plist=self.bindlist)

        self.lblDesc.set_text('Configurando detalles del sistema operativo ...')
        if not reconfigurar_paquetes(self.reconfpkgs):
            UserMessage(
                message='Ocurrió un error reconfigurando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
            )

        self.lblDesc.set_text('Removiendo instalador del sistema de archivos ...')
        if not desinstalar_paquetes(self.uninstpkgs):
            UserMessage(
                message='Ocurrió un error desinstalando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
            )

        self.lblDesc.set_text('Instalando gestor de arranque ...')
        if not preseed_debconf_values(
            mnt=self.mountpoint, debconflist=self.debconflist
            ):
            UserMessage(
                message='Ocurrió un error desinstalando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
            )
        if not instalar_paquetes(
            mnt = self.mountpoint, dest = '/root/debs', plist = self.instpkgs_burg
            ):
            UserMessage(
                message='Ocurrió un error desinstalando un paquete.',
                title='ERROR',
                mtype=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                c_1=gtk.RESPONSE_OK, f_1=sys.exit, p_1=(1,)
            )
        ProcessGenerator(
            'chroot {0} burg-install --force {1}'.format(
                self.mountpoint, self.metodo['disco'][0]
                )
            )
        ProcessGenerator(
            'chroot {0} update-burg'.format(self.mountpoint)
            )

        self.lblDesc.set_text('Generando imagen de arranque ...')
        ProcessGenerator(
            'chroot {0} /usr/sbin/mkinitramfs -o /boot/{1} {2}'.format(
                self.mountpoint, 'initrd.img-'+os.uname()[2], os.uname()[2]
                )
            )
        ProcessGenerator(
            'chroot {0} update-initramfs -u'.format(self.mountpoint)
            )

        self.lblDesc.set_text('Configurando interfaces de red ...')
        crear_etc_hostname(
            mnt=self.mountpoint, cfg='/etc/hostname', maq=self.maquina
            )
        crear_etc_hosts(
            mnt=self.mountpoint, cfg='/etc/hosts', maq=self.maquina
            )
        crear_etc_network_interfaces(
            mnt=self.mountpoint, cfg='/etc/network/interfaces'
            )

        self.lblDesc.set_text('Configurando teclado ...')
        crear_etc_default_keyboard(
            mnt=self.mountpoint, cfg='/etc/canaima-base/alternatives/keyboard',
            key=self.teclado
            )

        self.lblDesc.set_text('Configurando particiones, usuarios y grupos ...')
        crear_etc_fstab(
            mnt=self.mountpoint, cfg='/etc/fstab',
            mountlist=self.mountlist, cdroms=self.cdroms
            )
        ProcessGenerator('cp -f /etc/passwd {0}/etc/passwd'.format(self.mountpoint))
        ProcessGenerator('cp -f /etc/group {0}/etc/group'.format(self.mountpoint))
        ProcessGenerator('cp -f /etc/inittab {0}/etc/inittab'.format(self.mountpoint))
        ProcessGenerator('rm -rf {0}/etc/mtab'.format(self.mountpoint))
        ProcessGenerator('touch {0}/etc/mtab'.format(self.mountpoint))

        if self.oem:
            self.adm_user = 'root'
            self.adm_password = 'root'
            self.nml_user = 'canaima'
            self.nml_password = 'canaima'
            self.nml_name = 'Mantenimiento'

            instalar_paquetes(
                mnt = self.mountpoint, dest = '/root/debs',
                plist = self.instpkgs_cpp
                )

        else:
            self.adm_user = 'root'
            self.adm_password = self.passroot
            self.nml_user = self.usuario
            self.nml_password = self.passuser
            self.nml_name = self.nombre

        if self.chkgdm:
            instalar_paquetes(
                mnt = self.mountpoint, dest = '/root/debs',
                plist = self.instpkgs_cagg
                )

        self.lblDesc.set_text('Creando usuario administrador ...')
        ProcessGenerator('chroot {0} echo "{1}:{2}" > /tmp/passwd'.format(self.mountpoint, self.adm_user, self.adm_password))
        ProcessGenerator('chroot {0} /usr/sbin/chpasswd < /tmp/passwd'.format(self.mountpoint))
        ProcessGenerator('rm -rf {0}/tmp/passwd'.format(self.mountpoint))

        self.lblDesc.set_text('Creando usuario "{0}" ...'.format(self.nml_user))
        ProcessGenerator('chroot {0} /usr/sbin/userdel -r canaima'.format(self.mountpoint))
        ProcessGenerator('chroot {0} /usr/sbin/useradd -m -d /home/{1} {2} -s /bin/bash -c "{3}"'.format(self.mountpoint, self.nml_user, self.nml_user, self.nml_name))
        ProcessGenerator('chroot {0} echo "{1}:{2}" > /tmp/passwd'.format(self.mountpoint, self.nml_user, self.nml_password))
        ProcessGenerator('chroot {0} /usr/sbin/chpasswd < /tmp/passwd'.format(self.mountpoint))
        ProcessGenerator('rm -rf {0}/tmp/passwd'.format(self.mountpoint))

        if self.connection:
            self.lblDesc.set_text('Actualizando sistema operativo desde repositorios ...')
            ProcessGenerator('chroot {0} dhclient'.format(self.mountpoint))
            ProcessGenerator('chroot {0} aptitude update'.format(self.mountpoint))
            ProcessGenerator('chroot {0} aptitude full-upgrade'.format(self.mountpoint))

        self.lblDesc.set_text('Desmontando sistema de archivos ...')
        ProcessGenerator('umount -l {0}/dev/pts'.format(self.mountpoint))
        ProcessGenerator('umount -l {0}/dev'.format(self.mountpoint))
        ProcessGenerator('umount -l {0}/proc'.format(self.mountpoint))
        ProcessGenerator('umount -l {0}/sys'.format(self.mountpoint))
        ProcessGenerator('umount -l {0}'.format(self.mountpoint))
        ProcessGenerator('sync > /dev/null')

        self.lblDesc.set_text('Ninguna planta fue lastimada en la creación del estilo visual de este instalador.')

        self.visor.hide()
        self.w.anterior.show()
        self.w.siguiente.show()

