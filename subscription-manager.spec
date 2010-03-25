Name: subscription-manager      
Version: 0.21
Release: 1
Summary: Supported tools and libraries for subscription and repo Management       
Group:   System Environment/Base         
License: GPL       
Source0: %{name}-%{version}.tar.gz       
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires: python-dmidecode
Requires:  python-ethtool 
Requires:  python-simplejson
Requires:  m2crypto 
Requires: yum >= 3.2.19-15
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
BuildRequires: python-devel
BuildRequires: gettext
BuildRequires: intltool

%description
Subscription Manager package provides programs and libraries to allow users to manager subscriptions and repos from a unified entitlement or a deployment Platform.

%package -n subscription-manager-gnome
Summary: A GUI interface to manage Red Hat product subscriptions
Group: System Environment/Base
Requires: %{name} = %{version}-%{release}
Requires: pygtk2 pygtk2-libglade gnome-python2 gnome-python2-canvas
Requires: usermode-gtk

%description -n subscription-manager-gnome
subscription-manager-gnome contains a GTK+ graphical interface for configuring and registering a system with a Red Hat Entitlement platform and manage subscriptions.


%prep
%setup -q

%build
mkdir bin
cc src/rhsmcertd.c -o bin/rhsmcertd

%install
# TODO: Need clean/Makefile
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/share/rhsm
mkdir -p $RPM_BUILD_ROOT/usr/share/rhsm/gui
mkdir -p $RPM_BUILD_ROOT/usr/share/rhsm/gui/data
mkdir -p $RPM_BUILD_ROOT/usr/lib/yum-plugins/
mkdir -p $RPM_BUILD_ROOT/usr/sbin
mkdir -p $RPM_BUILD_ROOT/etc/rhsm
mkdir -p $RPM_BUILD_ROOT/etc/yum/pluginconf.d/
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man8/
mkdir -p $RPM_BUILD_ROOT/var/log/rhsm 
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/init.d
cp -R src/*.py $RPM_BUILD_ROOT/usr/share/rhsm
cp -R src/gui/*.py $RPM_BUILD_ROOT/usr/share/rhsm/gui
cp -R src/gui/data/* $RPM_BUILD_ROOT/usr/share/rhsm/gui/data/
cp -R src/plugin/*.py $RPM_BUILD_ROOT/usr/lib/yum-plugins/
cp src/subscription-manager-cli $RPM_BUILD_ROOT/usr/sbin
cp src/subscription-manager-gui $RPM_BUILD_ROOT/usr/sbin
cp etc-conf/rhsm.conf $RPM_BUILD_ROOT/etc/rhsm/
cp etc-conf/rhsmplugin.conf $RPM_BUILD_ROOT/etc/yum/pluginconf.d/
cp bin/* $RPM_BUILD_ROOT/%{_bindir}
cp src/rhsmcertd.init.d $RPM_BUILD_ROOT/%{_sysconfdir}/init.d/rhsmcertd
cp man/* $RPM_BUILD_ROOT/%{_mandir}/man8/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)

# dirs
%dir %{_datadir}/rhsm
%dir %{_datadir}/rhsm/gui
%dir %{_datadir}/rhsm/gui/data

#files
%{_datadir}/rhsm/__init__.py*
%{_datadir}/rhsm/connection.py*
%{_datadir}/rhsm/managercli.py*
%{_datadir}/rhsm/managerlib.py*
%{_datadir}/rhsm/repolib.py*
/usr/lib/yum-plugins/rhsmplugin.py*
%{_datadir}/rhsm/certificate.py*
%{_datadir}/rhsm/certlib.py*
%{_datadir}/rhsm/hwprobe.py*
%{_datadir}/rhsm/config.py*
%{_datadir}/rhsm/constants.py*
%{_datadir}/rhsm/logutil.py*
%{_datadir}/rhsm/OptionsCli.py*
%{_datadir}/rhsm/lock.py*
#%{_datadir}/rhsm/rhsmcertd.*
%attr(755,root,root) %{_sbindir}/subscription-manager-cli
%attr(700,root,root) %dir %{_var}/log/rhsm
%attr(755,root,root) %{_bindir}/rhsmcertd
%attr(755,root,root) %{_sysconfdir}/init.d/rhsmcertd

# config files
%attr(644,root,root) /etc/rhsm/rhsm.conf
%attr(644,root,root) /etc/yum/pluginconf.d/rhsmplugin.conf

%doc
%{_mandir}/man8/subscription-manager-cli.8*

%files -n subscription-manager-gnome
%defattr(-,root,root,-)
%{_datadir}/rhsm/gui/__init__.py* 
%{_datadir}/rhsm/gui/firstboot.py* 
%{_datadir}/rhsm/gui/managergui.py*  
%{_datadir}/rhsm/gui/messageWindow.py*  
%{_datadir}/rhsm/gui/data/standaloneH.glade  
%{_datadir}/rhsm/gui/data/subsgui.glade  
%{_datadir}/rhsm/gui/data/subsMgr.glade
%attr(755,root,root) %{_sbindir}/subscription-manager-gui


%post
chkconfig --add rhsmcertd
/sbin/service rhsmcertd start

%preun
if [ $1 = 0 ] ; then
   /sbin/service rhsmcertd stop >/dev/null 2>&1
   /sbin/chkconfig --del rhsmcertd
fi

%changelog
* Thu Mar 25 2010 Pradeep Kilambi <pkilambi@redhat.com> 
- Resolves: #568427
- Spec file clean up
- moving gnome tools to separate package

* Wed Mar 24 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.21-1
- Resolves: #568427
- event notification from add/remove and update subscription actions to main window
- error notification windows
- registration should now auto subscribe products and redirect to already-registered screen

* Mon Mar 22 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.20-1
- Resolves: #568427
- logging support
- changes to support identity cert parsing

* Fri Mar 19 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.19-1
- Resolves: #568427 
- Changes to support dynamic icon changes
- changes to support resteasy api changes
- fixed alignment issues in mainWindow

* Wed Mar 17 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.17-1
- Resolves:  #568427 - New registration/regtoken/add subscriptions screens

* Mon Mar 15 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.17-1
- Resolves:  #568426
- More changes to api proxy
- new gui screens 

* Thu Mar 11 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.16-1
- Resolves:  #568426 
- more updates to connection.py api flush down
- updates to new screens and layout in gui

* Mon Mar 08 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.14-1
- Resolves: #568426 - new build

* Wed Mar 03 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.12-1
- Resolves: #568433 - Flushed out hardware info
- man page for cli

* Mon Feb 22 2010 Pradeep Kilambi <pkilambi@redhat.com> 0.1-1
- packaging subscription-manager

