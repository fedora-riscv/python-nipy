# All tests run
%bcond_without tests

%global commit 35a5f5205ba2aa54f1f0524564a6f1f8dafb237f
%global snapdate 20230103

Name:           python-nipy
Version:        0.5.0^%(echo '%{commit}' | cut -b -7)git%{snapdate}
Release:        1%{?dist}
Summary:        Neuroimaging in Python FMRI analysis package

License:        BSD
URL:            https://nipy.org/nipy
Source0:        https://github.com/nipy/nipy/archive/%{commit}/nipy-%{commit}.tar.gz

# Ensure numpy is in install_requires, not only setup_requires
# https://github.com/nipy/nipy/pull/500
Patch:          https://github.com/nipy/nipy/pull/500.patch
# Remove a couple of unnecessary bundled dependencies
# https://github.com/nipy/nipy/pull/501
#   - configobj is not used anywhere
#   - argparse is present in the standard library from Python 2.7 onwards
Patch:          https://github.com/nipy/nipy/pull/501.patch
# Fix a typo introduced in PR#501
# https://github.com/nipy/nipy/pull/502
Patch:          https://github.com/nipy/nipy/pull/502.patch

BuildRequires:  gcc
BuildRequires:  flexiblas-devel
BuildRequires:  python3-devel

BuildRequires:  python3dist(setuptools)

# For re-generating C code as required by packaging guidelines; see also
# nipy/nipy/info.py
BuildRequires:  python3dist(cython) >= 0.12.1

# setup_requires (and install_requires with patch); see also nipy/nipy/info.py
BuildRequires:  python3dist(numpy) >= 1.14
# install_requires; see also nipy/nipy/info.py
BuildRequires:  python3dist(nibabel) >= 2
BuildRequires:  python3dist(scipy) >= 1
BuildRequires:  python3dist(sympy) >= 1
# Unbundled and added to install_requires in %%prep:
BuildRequires:  python3dist(six)
BuildRequires:  python3dist(transforms3d)

%if %{with tests}
# https://fedoraproject.org/wiki/Changes/DeprecateNose
BuildRequires:  python3dist(nose)
BuildRequires:  nipy-data
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
Requires:       python3dist(matplotlib)

Suggests:       nipy-data

%description -n python3-nipy %{common_description}

%prep
%autosetup -n nipy-%{commit} -p1

# Add dependencies on libraries that are unbundled downstream to the metadata:
line="requirement_kwargs['install_requires'].extend(['six', 'transforms3d'])"
sed -r -i "s/^(def main|setup)/# Unbundled:\\n${line}\\n&/" setup.py

# Some bundled pure-Python libraries have been replaced with dependencies:
#   - python3dist(transforms3d)
#   - python3dist(six)
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

find examples -type f -name '*.py' -exec sed -i '1{\@^#!/usr/bin/env python@d}' {} ';'



%build
export NIPY_EXTERNAL_LAPACK=1

# Regenerate the Cython files
make recythonize

%py3_build


%install
export NIPY_EXTERNAL_LAPACK=1

%py3_install

find %{buildroot}%{python3_sitearch} -name '*.so' -exec chmod 755 {} ';'

find %{buildroot}%{python3_sitearch}/nipy/ -name '*.py' -type f > tmp
while read lib
do
 sed -i '1{\@^#!/usr/bin/env python@d}' $lib
done < tmp
rm -f tmp


%check
%if %{with tests}
TESTING_DATA=(                                             \
nipy/testing/functional.nii.gz                             \
nipy/modalities/fmri/tests/spm_hrfs.mat                    \
nipy/modalities/fmri/tests/spm_dmtx.npz                    \
nipy/testing/anatomical.nii.gz                             \
nipy/algorithms/statistics/models/tests/test_data.bin      \
nipy/algorithms/diagnostics/tests/data/tsdiff_results.mat  \
nipy/modalities/fmri/tests/spm_bases.mat                   \
nipy/labs/spatial_models/tests/some_blobs.nii              \
nipy/modalities/fmri/tests/cond_test1.txt                  \
nipy/modalities/fmri/tests/dct_5.txt                       \
nipy/modalities/fmri/tests/dct_10.txt                      \
nipy/modalities/fmri/tests/dct_100.txt                     \
)

# It seems like this is checking some internals of sympy that were changed:
%global skip_tests test_implemented_function

pushd build/lib.*-*
  for i in ${TESTING_DATA[@]}
  do
    mkdir -p ./${i%/*}/
    cp -a ../../$i ./$i
  done
  PATH="%{buildroot}%{_bindir}:$PATH" \
      PYTHONPATH="%{buildroot}/%{python3_sitearch}" \
      nosetests-%{python3_version} -v %{?skip_tests:-e %{skip_tests}}
popd
%endif


%files -n python3-nipy
%license LICENSE
%doc README.rst
%doc AUTHOR
%doc THANKS
%doc examples/

%{_bindir}/nipy_3dto4d
%{_bindir}/nipy_4d_realign
%{_bindir}/nipy_4dto3d
%{_bindir}/nipy_diagnose
%{_bindir}/nipy_tsdiffana

%{python3_sitearch}/nipy*


%changelog
* Wed Feb 08 2023 Benjamin A. Beasley <code@musicinmybrain.net> - 0.5.0^19971cdgit20230102-1
- Update to a current snapshot (19971cd)
- Drop conditionals for EOL Fedoras and for EPEL8 and older
- Remove spurious BuildRequires on git-core
- Update URL to HTTPS
- Update description from upstream
- Handle dependencies more methodically

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
