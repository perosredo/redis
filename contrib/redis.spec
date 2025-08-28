# Redis 8.2.1 for EPEL 10
# Based on stable release tarball

%global upstream_ver    8.2.1
%global redis_user      redis
%global redis_group     %{redis_user}

%global debug_package %{nil}

Name:              redis
Version:           %{upstream_ver}
Release:           1%{?dist}
Summary:           A persistent key-value database
License:           RSALv2 and BSD and MIT
URL:               https://redis.io

Source0:           https://github.com/redis/redis/archive/%{upstream_ver}.tar.gz

BuildRequires:     gcc
BuildRequires:     gcc-c++
BuildRequires:     make
BuildRequires:     systemd-devel
BuildRequires:     openssl-devel >= 1.1
BuildRequires:     systemd-rpm-macros

Requires:          systemd
Requires(pre):     shadow-utils
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd

%description
Redis is an advanced key-value store. It is often referred to as a data
structure server since keys can contain strings, hashes, lists, sets and
sorted sets.

You can run atomic operations on these types, like appending to a string;
incrementing the value in a hash; pushing to a list; computing set
intersection, union and difference; or getting the member with highest
ranking in a sorted set.

In order to achieve its outstanding performance, Redis works with an
in-memory dataset. Depending on your use case, you can persist it either
by dumping the dataset to disk every once in a while, or by appending
each command to a log.

Redis also supports trivial-to-setup master-slave replication, with very
fast non-blocking first synchronization, auto-reconnection on net split
and so forth.

%package           devel
Summary:           Development header for Redis module development

%description       devel
Header files for developing Redis modules.

%prep
%setup -q -n %{name}-%{upstream_ver}

%build
export CFLAGS="$RPM_OPT_FLAGS -fPIC"
export LDFLAGS="$RPM_LD_FLAGS"

# Build all dependencies first
make %{?_smp_mflags} -C deps

# Build Redis using the standard build system
%make_build \
    PREFIX=%{_prefix} \
    INSTALL_BIN=%{_bindir} \
    OPTIMIZATION="$CFLAGS" \
    DEBUG="" \
    USE_SYSTEMD=yes \
    BUILD_TLS=yes \
    V=1

%install
%make_install PREFIX=%{buildroot}%{_prefix} INSTALL_BIN=%{buildroot}%{_bindir}

# Install configuration file
install -d %{buildroot}%{_sysconfdir}
install -p -m 0644 redis.conf %{buildroot}%{_sysconfdir}/%{name}.conf

# Modify config for systemd
sed -i 's/^daemonize yes/daemonize no/' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's/^# supervised auto/supervised systemd/' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's/^dir \.\/dir \/var\/lib\/redis/' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's/^pidfile .*$/pidfile \/var\/run\/redis\/redis-server.pid/' %{buildroot}%{_sysconfdir}/%{name}.conf
sed -i 's/^logfile .*$/logfile \/var\/log\/redis\/redis-server.log/' %{buildroot}%{_sysconfdir}/%{name}.conf

# Create systemd service file
install -d %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/%{name}.service << EOF
[Unit]
Description=Advanced key-value store
After=network.target
Documentation=http://redis.io/documentation, man:redis-server(1)

[Service]
Type=notify
ExecStart=/usr/bin/redis-server /etc/redis.conf
TimeoutStopSec=0
Restart=always
User=redis
Group=redis
RuntimeDirectory=redis
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

# Install headers for modules
install -d %{buildroot}%{_includedir}
install -p -m 0644 src/redismodule.h %{buildroot}%{_includedir}/

# Create directories
install -d %{buildroot}%{_localstatedir}/lib/%{name}
install -d %{buildroot}%{_localstatedir}/log/%{name}
install -d %{buildroot}%{_localstatedir}/run/%{name}

%pre
getent group %{redis_group} >/dev/null || groupadd -r %{redis_group}
getent passwd %{redis_user} >/dev/null || \
    useradd -r -g %{redis_group} -d %{_localstatedir}/lib/%{name} \
    -s /sbin/nologin -c "Redis Database Server" %{redis_user}
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%license COPYING
%doc README.md
%config(noreplace) %{_sysconfdir}/%{name}.conf
%{_unitdir}/%{name}.service
%{_bindir}/%{name}-*
%{_bindir}/%{name}-server
%attr(0755,%{redis_user},%{redis_group}) %dir %{_localstatedir}/lib/%{name}
%attr(0755,%{redis_user},%{redis_group}) %dir %{_localstatedir}/log/%{name}
%attr(0755,%{redis_user},%{redis_group}) %dir %{_localstatedir}/run/%{name}

%files devel
%{_includedir}/%{name}module.h

%changelog
* Wed Aug 28 2024 Petar Sredojevic <petar@sredojevic.ca> - 8.2.1-1
- Initial package for Redis 8.2.1
- Built for AlmaLinux 10 / EPEL 10