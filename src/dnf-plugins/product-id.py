from __future__ import print_function, division, absolute_import

#
# Copyright (c) 2015 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

import logging

from subscription_manager import logutil
from subscription_manager.productid import ProductManager
from subscription_manager.utils import chroot
from subscription_manager.injectioninit import init_dep_injection

from dnfpluginscore import _, logger
import dnf
import dnf.base
import dnf.sack
import librepo
import os
from rhsm import ourjson as json


class ProductId(dnf.Plugin):
    name = 'product-id'

    def __init__(self, base, cli):
        super(ProductId, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        self._enabled_repos = []

    def config(self):
        super(ProductId, self).config()
        # We are adding list of enabled repos to the list to be
        # able to access this list later in transaction hook
        for repo in self.base.repos.iter_enabled():
            self._enabled_repos.append(repo)

    def transaction(self):
        """
        Update product ID certificates.
        """
        if len(self.base.transaction) == 0:
            # nothing to update after empty transaction
            return

        try:
            init_dep_injection()
        except ImportError as e:
            logger.error(str(e))
            return

        logutil.init_logger_for_yum()
        chroot(self.base.conf.installroot)
        try:
            pm = DnfProductManager(self.base)
            pm.update_all(self._enabled_repos)
            logger.info(_('Installed products updated.'))
        except Exception as e:
            logger.error(str(e))


log = logging.getLogger('rhsm-app.' + __name__)


class DnfProductManager(ProductManager):

    CACHE_FILE = "/var/lib/rhsm/cache/package_repo_mapping.json"

    def __init__(self, base):
        self.base = base
        ProductManager.__init__(self)

    def update_all(self, enabled_repos):
        return self.update(self.get_certs_for_enabled_repos(enabled_repos),
                           self.get_active(),
                           True)

    def _download_productid(self, repo, tmpdir):
        handle = repo._handle_new_remote(tmpdir)
        handle.setopt(librepo.LRO_PROGRESSCB, None)
        handle.setopt(librepo.LRO_YUMDLIST, [self.PRODUCTID])
        res = handle.perform()
        return res.yum_repo.get(self.PRODUCTID, None)

    def get_certs_for_enabled_repos(self, enabled_repos):
        """
        Find enabled repos that are providing product certificates
        """
        lst = []

        # skip repo's that we don't have productid info for...
        for repo in enabled_repos:
            try:
                with dnf.util.tmpdir() as tmpdir:
                    fn = self._download_productid(repo, tmpdir)
                    if fn:
                        cert = self._get_cert(fn)
                        if cert is None:
                            log.debug('Repository %s does not provide cert' % repo.id)
                            continue
                        lst.append((cert, repo.id))
                    else:
                        # We have to look in all repos for productids, not just
                        # the ones we create, or anaconda doesn't install it.
                        self.meta_data_errors.append(repo.id)
            except Exception as e:
                log.warning("Error loading productid metadata for %s." % repo)
                log.exception(e)
                self.meta_data_errors.append(repo.id)

        if self.meta_data_errors:
            log.debug("Unable to load productid metadata for repos: %s",
                      self.meta_data_errors)
        return lst

    @staticmethod
    def _get_available():
        """Try to get list of available packages"""
        # FIXME: It is not safe to use two base objects in transaction hook.
        # Try to remove it, when dnf support getting list of available
        # packages during "dnf remove".
        with dnf.base.Base() as base:
            base.read_all_repos()
            base.fill_sack(load_system_repo=True, load_available_repos=True)
            available = base.sack.query().available()
        return available

    def write_avail_pkgs_cache(self, avail_pkgs):
        try:
            if not os.access(os.path.dirname(self.CACHE_FILE), os.R_OK):
                os.makedirs(os.path.dirname(self.CACHE_FILE))
            with open(self.CACHE_FILE, "w") as file:
                json.dump(avail_pkgs, file, default=json.encode)
            log.debug("Wrote cache: %s" % self.CACHE_FILE)
        except IOError as err:
            log.error("Unable to write cache: %s" % self.CACHE_FILE)
            log.exception(err)

    def read_avail_pkgs_cache(self):
        try:
            with open(self.CACHE_FILE) as file:
                json_str = file.read()
                data = json.loads(json_str)
            return data
        except IOError as err:
            log.error("Unable to read cache: %s" % self.CACHE_FILE)
            log.exception(err)
        except ValueError:
            # ignore json file parse errors, we are going to generate
            # a new as if it didn't exist
            pass
        return None

    # find the list of repo's that provide packages that
    # are actually installed.
    def get_active(self):
        """find repos that have packages installed"""

        # Create new sack to get fresh list of installed packages
        rpmdb_sack = dnf.sack._rpmdb_sack(self.base)
        q_installed = rpmdb_sack.query().installed()
        if hasattr(q_installed, "_na_dict"):
            # dnf 2.0
            installed_na = q_installed._na_dict()
        else:
            # dnf 1.0
            installed_na = q_installed.na_dict()

        available = self.base.sack.query().available()

        avail_pkgs = None
        if len(available) == 0:
            # When dnf does not provide list of available packages, then
            # try to get this list from cache
            avail_pkgs = self.read_avail_pkgs_cache()

            # When there is no cache, then try to force get this list from repositories
            if avail_pkgs is None:
                available = self._get_available()

        if avail_pkgs is None:
            avail_pkgs = available.filter(name=[k[0] for k in list(installed_na.keys())])
            avail_pkgs = [(p.name, p.arch, p.repoid) for p in avail_pkgs]
            self.write_avail_pkgs_cache(avail_pkgs)

        active = set()
        for p in avail_pkgs:
            if (p[0], p[1]) in installed_na:
                active.add(p[2])

        return active
