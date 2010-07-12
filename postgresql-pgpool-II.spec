%define short_name	pgpool-II
%define	major	0
%define	libname	%mklibname pcp %{major}
%define	devname	%mklibname pcp -d

Summary:	Pgpool is a connection pooling/replication server for PostgreSQL
Name:		postgresql-%{short_name}
Version:	2.3.3
Release:	%mkrel 1
License:	BSD
Group:		Databases
URL:		http://pgpool.projects.PostgreSQL.org
Source0:	http://pgfoundry.org/frs/download.php/2506/%{short_name}-%{version}.tar.gz
Source1:	pgpool.init
Source2:	pgpool.sysconfig
# (proyvind):	These are all patches of mine, briefly described in changelog for
#		2.3.3-1, eventually they should preferably make their way in some
#		form or another when I, or someone else who feels like it gets
#		around to it.. ;)
Patch0:		pgpool-II-2.3.3-string-format-fixes.patch
Patch1:		pgpool-II-2.3.3-pgpool.conf.patch
Patch2:		pgpool-II-2.3.3-daemon-stdout-stderr-logging.patch
Patch3:		pgpool-II-2.3.3-verify-child-pid-survival.patch
Requires(post,preun):	rpm-helper
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires:	postgresql-devel pam-devel openssl-devel
Requires:	postgresql-server
Obsoletes:	pgpool

%description
pgpool-II is a inherited project of pgpool (to classify from 
pgpool-II, it is sometimes called as pgpool-I). For those of 
you not familiar with pgpool-I, it is a multi-functional 
middle ware for PostgreSQL that features connection pooling, 
replication and load balancing functions. pgpool-I allows a 
user to connect at most two PostgreSQL servers for higher 
availability or for higher search performance compared to a 
single PostgreSQL server.

pgpool-II, on the other hand, allows multiple PostgreSQL 
servers (DB nodes) to be connected, which enables queries 
to be executed simultaneously on all servers. In other words, 
it enables "parallel query" processing. Also, pgpool-II can 
be started as pgpool-I by changing configuration parameters. 
pgpool-II that is executed in pgpool-I mode enables multiple 
DB nodes to be connected, which was not possible in pgpool-I. 

%package -n	%{libname}
Summary:	Library for pgpool-II
Group:		System/Libraries

%description -n	%{libname}
Library for pgpool-II.

%package -n	%{devname}
Summary:	Development headers for pgpool-II
Group:		Development/Libraries
Provides:	%{name}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}-%{release}

%description -n	%{devname}
Development headers and libraries for pgpool-II.

%prep
%setup -q -n %{short_name}-%{version}
%patch0 -p1 -b .str_fmt~
%patch1 -p1 -b .conf~
%patch2 -p1 -b .stdout_log~
%patch3 -p1 -b .verify_child_pid~

%build
%configure2_5x	--with-pgsql-includedir=%{_includedir}/pgsql \
		--with-pgsql-lib=%{_libdir}/pgsql \
		--disable-static \
		--with-pam \
		--with-openssl \
		--disable-rpath \
		--sysconfdir=%{_sysconfdir}/%{short_name}

%make

%install
rm -rf %{buildroot}
%makeinstall_std
install -d %{buildroot}%{_localstatedir}/run/pgpool

install -d %{buildroot}/var/log/postgres

install -d %{buildroot}%{_sysconfdir}/logrotate.d
tee %{buildroot}/%{_sysconfdir}/logrotate.d/pgpool <<EOH
/var/log/postgres/pgpool {
    notifempty
    missingok
    copytruncate
}
EOH

for i in %{buildroot}/%{_sysconfdir}/%{short_name}/*sample*; do mv $i `echo $i |sed -e 's#sample-##g' -e 's#\.sample##g'`; done

install -m755 %{SOURCE1} -D %{buildroot}%{_initrddir}/pgpool
install -m644 %{SOURCE2} -D %{buildroot}%{_sysconfdir}/sysconfig/pgpool

%clean
rm -rf %{buildroot}

%post
%_post_service pgpool

%preun
%_preun_service pgpool

%files
%defattr(-,root,root)
%doc README TODO COPYING AUTHORS ChangeLog NEWS
%doc doc/pgpool-en.html doc/pgpool.css doc/tutorial-en.html
%lang(ja) %doc README.euc_jp doc/pgpool-ja.html doc/tutorial-ja.html
%{_bindir}/pgpool
%{_bindir}/pcp_attach_node
%{_bindir}/pcp_detach_node
%{_bindir}/pcp_node_count
%{_bindir}/pcp_node_info
%{_bindir}/pcp_proc_count
%{_bindir}/pcp_proc_info
%{_bindir}/pcp_recovery_node
%{_bindir}/pcp_stop_pgpool
%{_bindir}/pcp_systemdb_info
%{_bindir}/pg_md5
%{_mandir}/man8/pgpool.8*
%dir %{_datadir}/%{short_name}
%{_datadir}/%{short_name}/system_db.sql
%{_datadir}/%{short_name}/pgpool.pam
%{_initrddir}/pgpool
%attr(700,postgres,postgres) %dir %{_localstatedir}/run/pgpool
%config(noreplace) %{_sysconfdir}/%{short_name}/*.conf*
%config(noreplace) %{_sysconfdir}/sysconfig/pgpool
%config(noreplace) %{_sysconfdir}/logrotate.d/pgpool

%files -n %{libname}
%defattr(-,root,root)
%{_libdir}/libpcp.so.%{major}*

%files -n %{devname}
%defattr(-,root,root)
%{_includedir}/pcp.h
%{_includedir}/pool_type.h
%{_libdir}/libpcp.so
%{_libdir}/libpcp.la

