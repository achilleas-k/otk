from main import process_include

expected_result = {
    'version': '1',
    'pipelines': [
        {
            'name': 'build',
            'runner': 'org.osbuild.fedora40',
            'stages': [
                {
                    'type': 'org.osbuild.rpm',
                    'inputs': {
                        'packages': {
                            'type': 'org.osbuild.files',
                            'origin': 'org.osbuild.source',
                            'references': [
                                {
                                    'id': 'sha256:7e635d208b2d3191973fbce9b2ee0a470204fa121270d9aa297ed5c3546f520b',
                                    'options': {
                                        'metadata': {
                                            'rpm.check_gpg': True
                                        }
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    'type': 'org.osbuild.selinux',
                    'options': {
                        'file_contexts': 'etc/selinux/targeted/contexts/files/file_contexts',
                        'labels': {
                            '/usr/bin/cp': 'system_u:object_r:install_exec_t:s0'
                        }
                    }
                }
            ]
        },
        {
            'name': 'os',
            'build': 'name:build',
            'stages': [
                {
                    'type': 'org.osbuild.something',
                    'options': {
                        'distroname': 'fedora40'
                    }
                }
            ]
        }
    ],
    'sources': {
        'org.osbuild.curl': {
            'items': {
                'sha256:aaa': {
                    'url': 'https://example.com'
                }
            }
        }
    }
}


def test_example():
    data = process_include("entrypoint.yaml", {})
    assert data == expected_result
