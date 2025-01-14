%define short_name	pgpool-II
%define	major	0
%define	libname	%mklibname pcp %{major}
%define	devname	%mklibname pcp -d

Summary:	Pgpool is a connection pooling/replication server for PostgreSQL
Name:		postgresql-%{short_name}
Version:	3.0
Release:	3
License:	BSD
Group:		Databases
URL:		https://pgpool.projects.PostgreSQL.org
Source0:	http://pgfoundry.org/frs/download.php/2506/%{short_name}-%{version}.tar.gz
Source1:	pgpool.init
Source2:	pgpool.sysconfig
Source3:	pgpool.conf.mirroring
Source4:	pgpool-copy-base-backup
Source5:	pgpool-archive_command
Source6:	pgpool-mirroring_failback
# (proyvind):	These are all patches of mine, briefly described in changelog for
#		2.3.3-1, eventually they should preferably make their way in some
#		form or another when I, or someone else who feels like it gets
#		around to it.. ;)
Patch1:		pgpool-II-3.0-pgpool.conf-mdkconf.patch
Patch2:		pgpool-II-3.0-logfile.patch
# there's a slight/minimal chance for a race condition through use of waitpid(2),
# TODO:
# <jbj> the easiest fix is to create a pipe to serialize the operation of parent <-> child
# <jbj> whoever runs 1st closes the pipe fd, whoever runs last blocks on the read and the close causes a 0b read (aka EOF)
# <jbj> ... usleep is just a bandaid because you don't know who long to wait. using pipe(2) to strictly force the parent <-> child ordering is the better fix.
# <jbj> but the usleep will "work" almost always.
Patch3:		pgpool-II-3.0-verify-child-pid-survival.patch
Patch4:		pgpool-II-2.3.3-support-libsetproctitle.patch
Patch5:		pgpool-II-3.0-recovery-script-customizations.patch
Patch6:		pgpool-II-3.0-custom-unix-socket-dir.patch
Patch7:		pgpool-II-3.0-fix-segfault-of-child-on-syntax-error-ext_query_prot.patch
Patch8:		pgpool-II-3.0-fix-md5-auth-bug.patch
Patch9:		pgpool-II-3.0-add-md5-username-option.patch
Requires(post,preun):	rpm-helper
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires:	postgresql-devel pam-devel openssl-devel
BuildRequires:	setproctitle-devel
Suggests:	postgresql-server postgresql-contrib-virtual
Provides:	%{short_name} = %{version}-%{release}
# This only being unversioned obsoletes only is fully intended as it's
# not meant to be an automatic, unvoluntarily upgrade of pgpool, but
# meant to replace it if user explicitly chooses to install the package
# it self.. So matching provides are excluded with intent as well.
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
Group:		Development/C
Provides:	%{name}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}-%{release}

%description -n	%{devname}
Development headers and libraries for pgpool-II.

%prep
%setup -q -n %{short_name}-%{version}
iconv -f iso-8859-1 -t utf-8 TODO -o TODO
%patch1 -p1 -b .mdkconf~
%patch2 -p1 -b .stdout_log~
%patch3 -p1 -b .verify_child_pid~
%patch4 -p1 -b .setproctitle~
%patch5 -p1 -b .recovery~
%patch6 -p1 -b .socketdir~
%patch7 -p1 -b .syntax_err_segfault~
%patch8 -p1 -b .md5_auth_bug~
%patch9 -p1 -b .md5_user_option~
autoreconf -fi
cp %{SOURCE4} sample/copy-base-backup
cp %{SOURCE5} sample/archive_command
cp %{SOURCE6} sample/mirroring_failback

%build
%configure2_5x	--with-pgsql-includedir=%{_includedir}/pgsql \
		--with-pgsql-libdir=%{_libdir}/pgsql \
		--disable-static \
		--with-pam \
		--with-openssl \
		--disable-rpath \
		--sysconfdir=%{_sysconfdir}/%{short_name}

%make
%make -C sql/pgpool-recovery
%make -C sql/pgpool-regclass

%install
%makeinstall_std
%makeinstall_std -C sql/pgpool-recovery
%makeinstall_std -C sql/pgpool-regclass

install -d %{buildroot}%{_localstatedir}/run/{pgpool,postgresql}

install -d %{buildroot}%{_sysconfdir}/logrotate.d
tee %{buildroot}/%{_sysconfdir}/logrotate.d/pgpool <<EOH
/var/log/postgres/pgpool {
    notifempty
    missingok
    copytruncate
}
EOH

for i in %{buildroot}/%{_sysconfdir}/%{short_name}/*sample*
	do mv $i `echo $i |sed -e 's#sample-##g' -e 's#\.sample##g'`
done
install -m644 %{SOURCE3} -D %{buildroot}%{_sysconfdir}/%{short_name}/pgpool.conf.mirroring
install -m755 %{SOURCE1} -D %{buildroot}%{_initrddir}/pgpool
install -m640 %{SOURCE2} -D %{buildroot}%{_sysconfdir}/sysconfig/pgpool
sed -e 's#/usr/local#/usr#g' -i sample/*
install -m644 sample/dist_def_pgbench.sql %{buildroot}%{_datadir}/%{short_name}
install -m644 sample/replicate_def_pgbench.sql %{buildroot}%{_datadir}/%{short_name}

for i in archive_command copy-base-backup mirroring_failback pgpool_recovery pgpool_recovery_pitr pgpool_remote_start; do
	install -m755 sample/$i %{buildroot}%{_datadir}/%{short_name}/$i
done

touch %{buildroot}%{_sysconfdir}/%{short_name}/pool_passwd

%posttrans
%create_ghostfile %{_sysconfdir}/%{short_name}/pool_passwd postgres postgres 644
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
%{_datadir}/%{short_name}/archive_command
%{_datadir}/%{short_name}/copy-base-backup
%{_datadir}/%{short_name}/mirroring_failback
%{_datadir}/%{short_name}/system_db.sql
%{_datadir}/%{short_name}/pgpool.pam
%{_datadir}/%{short_name}/pgpool_recovery_pitr
%{_datadir}/%{short_name}/dist_def_pgbench.sql
%{_datadir}/%{short_name}/pgpool_recovery
%{_datadir}/%{short_name}/pgpool_remote_start
%{_datadir}/%{short_name}/replicate_def_pgbench.sql
%{_datadir}/postgresql/contrib/pgpool-recovery.sql
%{_datadir}/postgresql/contrib/pgpool-regclass.sql
%{_initrddir}/pgpool
%{_libdir}/postgresql/pgpool-recovery.so
%{_libdir}/postgresql/pgpool-regclass.so
%attr(700,postgres,postgres) %dir %{_localstatedir}/run/pgpool
%attr(775,postgres,postgres) %dir %{_localstatedir}/run/postgresql
%dir %{_sysconfdir}/%{short_name}
%config(noreplace) %{_sysconfdir}/%{short_name}/*.conf*
%ghost %attr(644,postgres,postgres) %{_sysconfdir}/%{short_name}/pool_passwd
%attr(640,root,postgres) %config(noreplace) %{_sysconfdir}/sysconfig/pgpool
%config(noreplace) %{_sysconfdir}/logrotate.d/pgpool

%files -n %{libname}
%defattr(-,root,root)
%{_libdir}/libpcp.so.%{major}*

%files -n %{devname}
%defattr(-,root,root)
%{_includedir}/pcp.h
%{_includedir}/pool_type.h
%{_libdir}/libpcp.so

