%global vbox_ga_dir     /opt/VBoxGuestAdditions-%{version}

Name:           virtualbox-guest-additions
Version:        7.1.6
Release:        1%{?dist}
Summary:        VirtualBox Guest Additions for Linux
License:        GPLv3
URL:            https://www.virtualbox.org/

Source0:        https://download.virtualbox.org/virtualbox/%{version}/VBoxGuestAdditions_%{version}.iso
Source1:        vboxservice.service
Source2:        vboxclient.service
Source3:        60-vboxguest.rules
Source4:        mount.vboxsf

BuildRequires:  7zip
BuildRequires:  cpio
BuildRequires:  make
BuildRequires:  tar
BuildRequires:  systemd-rpm-macros

Requires:       systemd
Requires:       dkms
Requires:       kernel-devel
Requires:       gcc
Requires:       make

# VirtualBox guests are x86 only
ExclusiveArch:  x86_64

%description
VirtualBox Guest Additions provide closer integration between host and guest
systems. They offer features such as shared folders, seamless windows, better
video support, shared clipboard, and automated logins.

This package installs the VirtualBox Guest Additions from the official
VirtualBox ISO image for Enterprise Linux systems.

%prep
# Extract the ISO contents using 7z (no root privileges needed)
mkdir -p %{_builddir}/iso
7z x -o%{_builddir}/iso %{SOURCE0}
cp %{_builddir}/iso/VBoxLinuxAdditions.run %{_builddir}/
chmod +x %{_builddir}/VBoxLinuxAdditions.run

# Extract the run file contents
sh %{_builddir}/VBoxLinuxAdditions.run --noexec --keep --nox11 --target %{_builddir}/additions %{_builddir}/additions

%build
# Nothing to build; we repackage prebuilt binaries

%install
# Create directory structure
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sbindir}
mkdir -p %{buildroot}%{vbox_ga_dir}/bin
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_udevrulesdir}
mkdir -p %{buildroot}%{_libdir}/security
mkdir -p %{buildroot}%{_sysconfdir}/X11/xinit/xinitrc.d
mkdir -p %{buildroot}%{_sysconfdir}/xdg/autostart

ADDITIONS_DIR=%{_builddir}/additions

# Install guest additions binaries
for bin in VBoxService VBoxClient VBoxControl VBoxDRMClient; do
    if [ -f "$ADDITIONS_DIR/bin/$bin" ]; then
        install -m 0755 "$ADDITIONS_DIR/bin/$bin" %{buildroot}%{_bindir}/$bin
    fi
done

# Install VBoxService to sbindir
if [ -f "%{buildroot}%{_bindir}/VBoxService" ]; then
    mv %{buildroot}%{_bindir}/VBoxService %{buildroot}%{_sbindir}/VBoxService
fi

# Install mount helper
install -m 0755 %{SOURCE4} %{buildroot}%{_sbindir}/mount.vboxsf

# Install PAM module if available
find "$ADDITIONS_DIR" -name "pam_vbox.so" -exec install -m 0755 {} %{buildroot}%{_libdir}/security/ \; 2>/dev/null || \
    touch %{buildroot}%{_libdir}/security/pam_vbox.so

# Install systemd service files
install -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/vboxservice.service
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/vboxclient.service

# Install udev rules
install -m 0644 %{SOURCE3} %{buildroot}%{_udevrulesdir}/60-vboxguest.rules

# Install DKMS kernel module sources
mkdir -p %{buildroot}/usr/src/vboxguest-%{version}
find "$ADDITIONS_DIR" -name "vboxguest" -type d -exec cp -a {}/* %{buildroot}/usr/src/vboxguest-%{version}/ \; 2>/dev/null || true

%pre
getent group vboxsf >/dev/null || groupadd -r vboxsf

%post
%systemd_post vboxservice.service
%systemd_post vboxclient.service

# Set up DKMS modules if source is available
if [ -d /usr/src/vboxguest-%{version} ] && command -v dkms >/dev/null 2>&1; then
    dkms add -m vboxguest -v %{version} >/dev/null 2>&1 || true
    dkms build -m vboxguest -v %{version} >/dev/null 2>&1 || true
    dkms install -m vboxguest -v %{version} >/dev/null 2>&1 || true
fi

%preun
%systemd_preun vboxservice.service
%systemd_preun vboxclient.service

if [ $1 -eq 0 ] && command -v dkms >/dev/null 2>&1; then
    dkms remove -m vboxguest -v %{version} --all >/dev/null 2>&1 || true
fi

%postun
%systemd_postun_with_restart vboxservice.service
%systemd_postun_with_restart vboxclient.service

%files
%{_bindir}/VBoxClient
%{_bindir}/VBoxControl
%{_bindir}/VBoxDRMClient
%{_sbindir}/VBoxService
%{_sbindir}/mount.vboxsf
%{_libdir}/security/pam_vbox.so
%{_unitdir}/vboxservice.service
%{_unitdir}/vboxclient.service
%{_udevrulesdir}/60-vboxguest.rules
/usr/src/vboxguest-%{version}

%changelog
* Tue Feb 10 2026 junland - 7.1.6-1
- Initial package for Enterprise Linux
