Vagrant.configure(2) do |config|
  config.vm.guest = :freebsd
  config.vm.box = "freebsd/FreeBSD-11.1-RELEASE"
  config.vm.synced_folder ".", "/app", nfs: true
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.base_mac = "080027D14C66"
  config.vm.network "private_network", ip: "192.168.50.4"
  config.vm.network "forwarded_port", guest: 8000, host: 8000,
      auto_correct: true
  config.vm.provider "virtualbox" do |vb|
    vb.name = "mfctracker-dev"
    vb.customize ["modifyvm", :id, "--memory", "2048"]
    vb.customize ["modifyvm", :id, "--hwvirtex", "on"]
    vb.customize ["modifyvm", :id, "--audio", "none"]
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    vb.customize ["modifyvm", :id, "--nictype2", "virtio"]
  end
  config.ssh.shell = "sh"
  config.vm.provision "shell", inline: <<-SHELL
    pkg install -y vim-lite py27-virtualenvwrapper postgresql96-server subversion p5-ack openldap-sasl-client
    sysrc postgresql_enable=YES
    service postgresql initdb
    service postgresql start

    psql -U postgres -c 'create user vagrant'
    psql -U postgres -c 'alter user vagrant with superuser'
    psql -U vagrant -c "drop database if exists mfctracker_dev;" template1
    psql -U vagrant "create database mfctracker_dev;" template1

    su vagrant -c "virtualenv ~/.venv/mfctracker"
    echo "set mouse=" > ~vagrant/.vimrc
    chown vagrant ~vagrant/.vimrc
    echo "setenv DJANGO_SETTINGS_MODULE mfctracker.settings.development" >> ~vagrant/.cshrc
    echo "source ~vagrant/.venv/mfctracker/bin/activate.csh" >> ~vagrant/.cshrc
    su vagrant -c "pip install -r /app/requirements-dev.txt"
  SHELL
end
