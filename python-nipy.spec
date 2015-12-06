%global modname nipy

%global _docdir_fmt %{name}

# Disable one of tests due to:
# https://github.com/nipy/nipy/issues/382
%if 0%{?__isa_bits} != 64
%global skip_tests test_mu2tet
%endif

Name:           python-%{modname}
Version:        0.4.0
Release:        3%{?dist}
Summary:        Neuroimaging in Python FMRI analysis package

License:        BSD
URL:            http://nipy.org/nipy
Source0:        https://github.com/nipy/nipy/archive/%{version}/%{modname}-%{version}.tar.gz
# https://github.com/nipy/nipy/pull/381
Patch0:         0001-test_olsR-use-assert_array_almost_equal-instead.patch
BuildRequires:  git-core
BuildRequires:  gcc
BuildRequires:  lapack-devel blas-devel atlas-devel

%description
Neuroimaging tools for Python.

The aim of NIPY is to produce a platform-independent Python environment for the
analysis of functional brain imaging data using an open development model.

%package -n python2-%{modname}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{modname}}
BuildRequires:  python2-devel python-setuptools
BuildRequires:  numpy scipy python2-nibabel sympy
BuildRequires:  Cython
# Test deps
BuildRequires:  python2-nose
BuildRequires:  python2-six python2-transforms3d
BuildRequires:  nipy-data
Requires:       numpy scipy python2-nibabel sympy
Requires:       python2-six python2-transforms3d
Requires:       python-matplotlib
Suggests:       nipy-data

%description -n python2-%{modname}
Neuroimaging tools for Python.

The aim of NIPY is to produce a platform-independent Python environment for the
analysis of functional brain imaging data using an open development model.

Python 2 version.

%package -n python3-%{modname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{modname}}
BuildRequires:  python3-devel python3-setuptools
BuildRequires:  python3-numpy python3-scipy python3-nibabel python3-sympy
BuildRequires:  python3-Cython
# Test deps
BuildRequires:  python3-nose
BuildRequires:  python3-six python3-transforms3d
BuildRequires:  nipy-data
Requires:       python3-numpy python3-scipy python3-nibabel python3-sympy
Requires:       python3-six python3-transforms3d
Requires:       python3-matplotlib
Suggests:       nipy-data

%description -n python3-%{modname}
Neuroimaging tools for Python.

The aim of NIPY is to produce a platform-independent Python environment for the
analysis of functional brain imaging data using an open development model.

Python 3 version.

%prep
%autosetup -n %{modname}-%{version} -p1 -Sgit

# Hard fix for bundled libs
find -type f -name '*.py' -exec sed -i \
  -e "s/from \.*externals.six/from six/"                             \
  -e "s/from nipy.externals.six/from six/"                           \
  -e "s/from nipy.externals import six/import six/"                  \
  -e "s/from nipy.externals.argparse/from argparse/"                 \
  -e "s/import nipy.externals.argparse as argparse/import argparse/" \
  -e "s/from \.*externals.transforms3d/from transforms3d/"           \
  {} ';'
find scripts/ -type f -exec sed -i \
  -e "s/from nipy.externals.argparse/from argparse/"                 \
  -e "s/import nipy.externals.argparse as argparse/import argparse/" \
  {} ';'
sed -i -e "/config.add_subpackage(.externals.)/d" nipy/setup.py
rm -vrf nipy/externals/
rm -rf lib/lapack_lite/

find examples -type f -name '*.py' -exec sed -i '1{\@^#!/usr/bin/env python@d}' {} ';'

%build
export NIPY_EXTERNAL_LAPACK=1

%py2_build
%py3_build

%install
export NIPY_EXTERNAL_LAPACK=1

%py3_install
%py2_install

find %{buildroot}%{python2_sitearch} -name '*.so' -exec chmod 755 {} ';'
find %{buildroot}%{python3_sitearch} -name '*.so' -exec chmod 755 {} ';'

find %{buildroot}%{python2_sitearch}/%{modname}/ %{buildroot}%{python3_sitearch}/%{modname}/ -name '*.py' -type f > tmp
while read lib
do
 sed -i '1{\@^#!/usr/bin/env python@d}' $lib
done < tmp
rm -f tmp

%check
TESTING_DATA=( \
nipy/testing/functional.nii.gz                             \
nipy/modalities/fmri/tests/spm_hrfs.mat                    \
nipy/modalities/fmri/tests/spm_dmtx.npz                    \
nipy/testing/anatomical.nii.gz                             \
nipy/algorithms/statistics/models/tests/test_data.bin      \
nipy/algorithms/diagnostics/tests/data/tsdiff_results.mat  \
nipy/modalities/fmri/tests/spm_bases.mat                   \
)

pushd build/lib.*-%{python2_version}
  for i in ${TESTING_DATA[@]}
  do
    mkdir -p ./${i%/*}/
    cp -a ../../$i ./$i
  done
  nosetests-%{python2_version} -v %{?skip_tests:-e %{skip_tests}} -I test_scripts.py
popd

pushd build/lib.*-%{python3_version}
  for i in ${TESTING_DATA[@]}
  do
    mkdir -p ./${i%/*}/
    cp -a ../../$i ./$i
  done
  PATH="%{buildroot}%{_bindir}:$PATH" nosetests-%{python3_version} -v %{?skip_tests:-e %{skip_tests}}
popd

%files -n python2-%{modname}
%license LICENSE
%doc README.rst AUTHOR THANKS examples
%{python2_sitearch}/%{modname}*

%files -n python3-%{modname}
%license LICENSE
%doc README.rst AUTHOR THANKS examples
%{_bindir}/nipy_3dto4d
%{_bindir}/nipy_4d_realign
%{_bindir}/nipy_4dto3d
%{_bindir}/nipy_diagnose
%{_bindir}/nipy_tsdiffana
%{python3_sitearch}/%{modname}*

%changelog
* Sun Nov 29 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-3
- Use one directory for building

* Sat Nov 28 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-2
- Do not use obsolete py3dir
- Have only one binary

* Sun Nov 01 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.0-1
- Initial package
