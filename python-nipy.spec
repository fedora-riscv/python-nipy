# All tests run
%bcond_without tests
# Sphinx-generated HTML documentation is not suitable for packaging; see
# https://bugzilla.redhat.com/show_bug.cgi?id=2006555 for discussion.
#
# We can generate PDF documentation as a substitute.
#
# Currently, there are several issues that still prevent us from successfully
# building the documentation even with a few obvious patches. See:
# https://github.com/nipy/nipy/pull/503#issuecomment-1421508175
%bcond_with doc_pdf

%global commit 9512cd93b7215b4c750be3968a600c06f2bd22f6
%global snapdate 20230206

Name:           python-nipy
Version:        0.5.0^%(echo '%{commit}' | cut -b -7)git%{snapdate}
Release:        1%{?dist}
Summary:        Neuroimaging in Python FMRI analysis package

License:        BSD-3-Clause
URL:            https://nipy.org/nipy
Source0:        https://github.com/nipy/nipy/archive/%{commit}/nipy-%{commit}.tar.gz

# Man pages hand-written for Fedora in groff_man(7) format based on --help
Source10:       nipy_3dto4d.1
Source11:       nipy_4d_realign.1
Source12:       nipy_4dto3d.1
Source13:       nipy_diagnose.1
Source14:       nipy_tsdiffana.1

# Ensure numpy is in install_requires, not only setup_requires
# https://github.com/nipy/nipy/pull/500
Patch:          https://github.com/nipy/nipy/pull/500.patch
# Account for nibabel 5.0.0 removal of .py3k shim - use numpy.compat.py3k
# https://github.com/nipy/nipy/pull/498
# https://salsa.debian.org/med-team/nipy/-/blob/12a4fbea8c99c1e5dc07ee81bc3da1a450617050/debian/patches/nibabel5.0.0.patch
# Latest version from Debian rebased on the commit that is packaged.
Patch:          0001-Account-for-nibabel-5.0.0-removal-of-.py3k-shim-use-.patch
# Unbundle six
# https://github.com/nipy/nipy/pull/504
Patch:          https://github.com/nipy/nipy/pull/504/commits/a6de01c7484114aa52847edc400a386743e60c42.patch

BuildRequires:  gcc
BuildRequires:  flexiblas-devel
BuildRequires:  python3-devel

BuildRequires:  python3dist(setuptools)
# Imported in setup.py
BuildRequires:  python3dist(numpy)
#BuildRequires:  python3dist(six)

# For re-generating C code as required by packaging guidelines; see also
# nipy/nipy/info.py
BuildRequires:  python3dist(cython) >= 0.12.1

# A weak dependency; may enable more tests
BuildRequires:  python3dist(matplotlib)

%if %{with tests}
# https://fedoraproject.org/wiki/Changes/DeprecateNose
BuildRequires:  python3dist(nose)
BuildRequires:  nipy-data
# An indirect dependency, via nibabel.testing (for nibabel 5.x)
BuildRequires:  python3dist(pytest)
%endif

%if %{with doc_pdf}
BuildRequires:  graphviz
BuildRequires:  latexmk
BuildRequires:  make
BuildRequires:  python3-ipython-sphinx
BuildRequires:  python3-sphinx-latex
# Optional documentation dependency
BuildRequires:  python3dist(vtk)
%endif

%global _docdir_fmt %{name}

%global common_description %{expand:
Neuroimaging tools for Python.

The aim of NIPY is to produce a platform-independent Python environment for the
analysis of functional brain imaging data using an open development model.

In NIPY we aim to:

• Provide an open source, mixed language scientific programming environment
  suitable for rapid development.
• Create software components in this environment to make it easy to develop
  tools for MRI, EEG, PET and other modalities.
• Create and maintain a wide base of developers to contribute to this platform.
• Maintain and develop this framework as a single, easily installable bundle.}

%description %{common_description}


%package -n python3-nipy
Summary:        %{summary}

# Adds various plotting functionality, but not an “official” dependency
Recommends:     python3dist(matplotlib)

Suggests:       nipy-data

# The nipy.algorithms.statistics.models subpackage was forked from an
# undetermined version of scipy.stats.models in commit 55a9162 on 2011-09-13;
# before this, the upstream version was monkey-patched via
# nipy.fixes.scipy.stats.models.
Provides:       bundled(python3dist(scipy))

%description -n python3-nipy %{common_description}


%package doc
Summary:        Documentation and examples for python-nipy

BuildArch:      noarch

Requires:       nipy-data

%description doc
%{summary}.


%prep
%autosetup -n nipy-%{commit} -p1

# Add dependencies on libraries that are unbundled downstream to the metadata:
line="requirement_kwargs['install_requires'].extend(['transforms3d'])"
sed -r -i "s/^(def main|setup)/# Unbundled:\\n${line}\\n&/" setup.py

# Some bundled pure-Python libraries have been replaced with dependencies:
#   - python3dist(transforms3d)
# Begin by removing the subpackage for bundled dependencies:
rm -vrf nipy/externals/
# Now fix the imports. The find-then-modify pattern keeps us from discarding
# mtimes on any sources that do not need modification.
find . -type f -exec gawk \
    '/(from|import) (\.+|nipy\.)externals/ { print FILENAME }' '{}' '+' |
   xargs -r -t sed -r -i \
       -e 's/(from (nipy|\.*)\.externals )import/import/' \
       -e 's/from ((nipy|\.*)\.externals\.)([^ ]+) import/from \3 import/'
sed -r -i '/config\.add_subpackage\(.externals.\)/d' nipy/setup.py

# Remove bundled lapack
rm -rf lib/lapack_lite/

# Remove pre-generated Cython C sources
grep -FrlI 'Generated by Cython' . | xargs -r rm -vf

%py3_shebang_fix examples

cp -p nipy/algorithms/statistics/models/LICENSE.txt scipy-LICENSE.txt

# Remove doc dependency version pins, which we cannot respect
sed -r -i -e 's/(,<.*)$//' -e 's/==/>=/' doc-requirements.txt
# We don’t have a python-nose3 package (a fork and drop-in replacement for the
# deprecated python-nose). We also shouldn’t depend on the deprecated
# python-mock package if we can help it.
sed -r -i 's/^(nose3|mock)\b/# &/' dev-requirements.txt


%generate_buildrequires
%pyproject_buildrequires %{?with_doc_pdf:doc-requirements.txt}


%build
export NIPY_EXTERNAL_LAPACK=1

# Regenerate the Cython files
%make_build recythonize PYTHON='%{python3}'

%pyproject_wheel

%if %{with doc_pdf}
PYTHONPATH="%{pyproject_build_lib}" PYTHON='%{python3}' \
   %make_build -C doc latex SPHINXOPTS='%{?_smp_mflags}'
%make_build -C doc/dist/latex LATEXMKOPTS='-quiet'
%endif


%install
export NIPY_EXTERNAL_LAPACK=1

%pyproject_install
%pyproject_save_files nipy

install -t '%{buildroot}%{_mandir}/man1' -m 0644 -p -D \
    '%{SOURCE10}' '%{SOURCE11}' '%{SOURCE12}' '%{SOURCE13}' '%{SOURCE14}'


%check
%if %{with tests}
mkdir -p for_testing
cd for_testing
PATH="%{buildroot}%{_bindir}:${PATH}" \
    PYTHONPATH='%{buildroot}%{python3_sitearch}' \
    PYTHONDONTWRITEBYTECODE=1 \
    %{python3} ../tools/nipnost --verbosity=3 nipy
%endif


%files -n python3-nipy -f %{pyproject_files}
%license LICENSE
%license scipy-LICENSE.txt

%{_bindir}/nipy_3dto4d
%{_bindir}/nipy_4d_realign
%{_bindir}/nipy_4dto3d
%{_bindir}/nipy_diagnose
%{_bindir}/nipy_tsdiffana

%{_mandir}/man1/nipy_3dto4d.1*
%{_mandir}/man1/nipy_4d_realign.1*
%{_mandir}/man1/nipy_4dto3d.1*
%{_mandir}/man1/nipy_diagnose.1*
%{_mandir}/man1/nipy_tsdiffana.1*


%files doc
%license LICENSE
%license scipy-LICENSE.txt

%doc AUTHOR
%doc Changelog
%doc README.rst
%doc THANKS

%if %{with doc_pdf}
%doc doc/dist/latex/nipy.pdf
%endif

%doc examples/


%changelog
* Wed Feb 08 2023 Benjamin A. Beasley <code@musicinmybrain.net> - 0.5.0^19971cdgit20230102-1
- Update to a current snapshot (9512cd9)
- Drop conditionals for EOL Fedoras and for EPEL8 and older
- Remove spurious BuildRequires on git-core
- Update URL to HTTPS
- Update description from upstream
- Handle dependencies more methodically
- Allow the examples to retain shebangs (but do fix them)
- Split docs/examples into a -doc subpackage and depend on nipy-data
- Add Changelog to the documentation
- Simplify the tests to match .travis.yml
- Remove generated Cython files in prep to prove they are re-generated
- Downgrade matplotlib to a weak dep. and add it as a BR
- Properly indicate partial scipy bundling
- Update License to SPDX
- Port to pyproject-rpm-macros
- Add man pages for the command-line tools
- Add some support for PDF documentation, but do not enable it yet
- Fix compatibility with nibabel 5.0.0
- Unbundle six via a PR/patch to upstream rather than downstream-only

* Fri Jan 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Fri Jul 22 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Wed Jun 22 2022 Charalampos Stratakis <cstratak@redhat.com> - 0.5.0-5
- Fix FTBFS with Python 3.11 and setuptools >= 62.1.0
Resolves: rhbz#2099030, rhbz#2097101

* Fri Jun 17 2022 Python Maint <python-maint@redhat.com> - 0.5.0-4
- Rebuilt for Python 3.11

* Fri Jan 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Jul 23 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Sun Jul 04 2021 Ankur Sinha <ankursinha AT fedoraproject DOT org> - 0.5.0-1
- Update to latest release
- remove unneeded explicity provides
- remove s390x test exlusions
- Enable all tests

* Fri Jun 04 2021 Python Maint <python-maint@redhat.com> - 0.4.2-13
- Rebuilt for Python 3.10

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sun Aug 16 2020 Iñaki Úcar <iucar@fedoraproject.org> - 0.4.2-11
- https://fedoraproject.org/wiki/Changes/FlexiBLAS_as_BLAS/LAPACK_manager

* Thu Aug 13 2020 Ankur Sinha <ankursinha AT fedoraproject DOT org> - 0.4.2-10
- Temporarily disable tests
- #1800845

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-9
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 0.4.2-7
- Rebuilt for Python 3.9

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 0.4.2-5
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.4.2-4
- Rebuilt for Python 3.8

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Aug 14 2018 Miro Hrončok <mhroncok@redhat.com> - 0.4.2-1
- Update to 0.4.2
- Remove python2 subpackage

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.1-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.4.1-6
- Rebuilt for Python 3.7

* Mon Mar 26 2018 Iryna Shcherbina <ishcherb@redhat.com> - 0.4.1-5
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sun Feb 12 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0.4.1-1
- Update to latest version

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 0.4.0-7
- Rebuild for Python 3.6

* Sat Oct 15 2016 Peter Robinson <pbrobinson@fedoraproject.org> - 0.4.0-6
- rebuilt for matplotlib-2.0.0

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.0-5
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sun Nov 29 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-3
- Use one directory for building

* Sat Nov 28 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-2
- Do not use obsolete py3dir
- Have only one binary

* Sun Nov 01 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-1
- Initial package
