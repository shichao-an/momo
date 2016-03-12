import os
import yaml
from momo.utils import run_cmd, mkdir_p, utf8_encode
from momo.plugins.base import Plugin


class Mkdocs(Plugin):
    mkdocs_configs = {
        'theme': 'readthedocs',
    }
    momo_configs = {
        'page_level': 1,
        'attr_page': False
    }

    def setup(self):
        configs = self.settings.plugins.get('mkdocs', {})
        self.mkdocs_configs['site_name'] = self.settings.bucket.name
        for k in configs:
            if not k.startswith('momo_'):
                self.mkdocs_configs[k] = configs[k]
        for k in configs:
            if k.startswith('momo_'):
                self.momo_configs[k] = configs[k]
        self.mkdocs_dir = os.path.join(self.settings.settings_dir, 'mkdocs')
        self.docs_dir = os.path.join(self.mkdocs_dir, 'docs')
        self.site_dir = os.path.join(self.mkdocs_dir, 'site')
        mkdir_p(self.mkdocs_dir)
        mkdir_p(self.docs_dir)
        mkdir_p(self.site_dir)

    def _get_pages(self, root, level=0):
        if level == self.momo_configs['page_level']:
            filename = self._make_page(root)
            return filename
        else:
            pages = [
                {elem.name: self._get_pages(elem, level + 1)}
                for elem in root.svals
            ]
            return pages

    def _make_page(self, elem):
        res = '%s.md' % os.path.join(*elem.path)
        filename = os.path.join(self.docs_dir, res)
        buf = []
        with open(filename, 'w') as f:
            buf.append(self._make_title(elem))
            buf.append(self._make_attrs(elem))
            buf.append(self._make_nodes(elem))
            f.write(utf8_encode('\n'.join(buf)))
        return res

    def _make_title(self, elem):
        return utf8_encode('## %s' % elem.name)

    def _make_attrs(self, elem):
        buf = []
        buf.append('### Attributes')
        for attr in elem.attr_svals:
            buf.append('- %s: %s' % (attr.name, attr.content))
        return '\n'.join(buf)

    def _make_nodes(self, elem):
        buf = []
        buf.append('### Nodes')
        for node in elem.node_svals:
            buf.append('- %s' % (node.name))
        return '\n'.join(buf)

    def _make_mkdocs_yml(self):
        mkdocs_yml = os.path.join(self.mkdocs_dir, 'mkdocs.yml')
        with open(mkdocs_yml, 'w') as f:
            yaml.dump(self.mkdocs_configs, f, default_flow_style=False,
                      allow_unicode=True)

    def _make_index_page(self):
        res = 'index.md'
        filename = os.path.join(self.docs_dir, res)
        buf = []
        buf.append('## Home')
        buf.append('Welcome to momo!')
        with open(filename, 'w') as f:
            f.write('\n'.join(buf))
        return res

    def _serve(self):
        os.chdir(self.mkdocs_dir)
        run_cmd('mkdocs serve')

    def run(self):
        pages = self._get_pages(self.settings.bucket.root)
        self.mkdocs_configs['pages'] = [
            {'Home': self._make_index_page()},
            {'Root': pages},
        ]
        self._make_mkdocs_yml()
        self._serve()


plugin = Mkdocs()
