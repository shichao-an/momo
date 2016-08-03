import os
import shutil
import yaml
import glob
from momo.utils import run_cmd, mkdir_p, utf8_encode, txt_type
from momo.plugins.base import Plugin


class Mkdocs(Plugin):
    mkdocs_configs = {
        'theme': 'readthedocs',
    }
    momo_configs = {
        'momo_page_level': 1,
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

        self.mkdocs_root_dir = os.path.join(self.settings.settings_dir,
                                            'mkdocs')
        self.mkdocs_dir = os.path.join(self.mkdocs_root_dir,
                                       self.settings.bucket.name)
        self.docs_dir = os.path.join(self.mkdocs_dir, 'docs')
        self.site_dir = os.path.join(self.mkdocs_dir, 'site')
        if os.path.exists(self.docs_dir):
            shutil.rmtree(self.docs_dir)
        mkdir_p(self.docs_dir)
        mkdir_p(self.site_dir)
        assets = glob.glob(os.path.join(self.mkdocs_dir, '*'))
        for asset in assets:
            filename = os.path.basename(asset)
            if filename not in set(['docs', 'site', 'mkdocs.yml']):
                os.symlink(asset, os.path.join(self.docs_dir, filename))

    def _get_pages(self, root, level=0):
        if level == self.momo_configs['momo_page_level']:
            filename = self._make_page(root)
            return filename
        else:
            pages = [
                {'Index': self._make_index_page(root, level + 1)}
            ]
            pages += [
                {elem.name: self._get_pages(elem, level + 1)}
                for elem in root.node_svals
            ]
            return pages

    def _make_page(self, elem):
        res = '%s.md' % os.path.join(*elem.path)
        filename = os.path.join(self.docs_dir, res)
        dirname = os.path.dirname(filename)
        if dirname:
            mkdir_p(dirname)
        buf = []
        with open(filename, 'w') as f:
            buf.append(self._make_title(elem))
            buf.append(self._make_attrs(elem))
            buf.append(self._make_nodes(elem))
            f.write(utf8_encode('\n'.join(buf)))
        return res

    def _make_index_page(self, elem, level):
        base = os.path.join(*elem.path) if elem.path else ''
        res = os.path.join(base, 'index.md')
        filename = os.path.join(self.docs_dir, res)
        dirname = os.path.dirname(filename)
        if dirname:
            mkdir_p(dirname)
        buf = []
        with open(filename, 'w') as f:
            buf.append(self._make_title(elem))
            buf.append(self._make_attrs(elem))
            buf.append(self._make_nodes(elem, index=True, level=level))
            f.write(utf8_encode('\n'.join(buf)))
        return res

    def _make_title(self, elem):
        return '# %s' % elem.name

    def _make_attrs(self, elem):
        buf = []
        buf.append('### Attributes')
        for attr in elem.attr_svals:
            buf.append('\n')
            buf.append('- %s:%s' % (attr.name, self._make_attr_content(attr)))
        return '\n'.join(buf)

    def _make_attr_content(self, attr):
        buf = []
        if attr.has_items:
            buf.append('\n')
            for i, item in enumerate(attr.content, start=1):
                buf.append('    - %s[%d]: %s' % (attr.name, i,
                           self._make_link(item)))
        else:
            buf.append(' %s' % self._make_object(attr))
        return '\n'.join(buf)

    def _make_object(self, attr):
        name = attr.name
        content = attr.content
        if name.lower() in ('url', 'link'):
            return self._make_link(content)
        elif name.lower() in ('image', 'picture', 'photo'):
            return self._make_image(content)
        else:
            return self._make_link(content)
        return content

    def _make_link(self, content):
        if isinstance(content, txt_type) and content.startswith('http'):
            content = '[%s](%s)' % (content, content)
        return content

    def _make_image(self, content):
        res = '\n\n'
        if isinstance(content, txt_type) and content.startswith('http'):
            res += '[![image]({image})]({image} "image")'.format(image=content)
        return res

    def _make_nodes(self, elem, index=False, level=None):
        buf = []
        if not index:
            for node in elem.node_svals:
                buf.append('## %s' % (node.name))
                buf.append(self._make_attrs(node))
        else:
            buf.append('### Nodes')
            for node in elem.node_svals:
                if level == self.momo_configs['momo_page_level']:
                    buf.append('- [%s](%s.md)' % (node.name, node.name))
                else:
                    buf.append('- [%s](%s/index.md)' % (node.name, node.name))
        return '\n'.join(buf)

    def _make_mkdocs_yml(self):
        mkdocs_yml = os.path.join(self.mkdocs_dir, 'mkdocs.yml')
        with open(mkdocs_yml, 'w') as f:
            yaml.dump(self.mkdocs_configs, f, default_flow_style=False,
                      allow_unicode=True)

    def _make_home_page(self):
        res = 'index.md'
        filename = os.path.join(self.docs_dir, res)
        buf = []
        buf.append('# Home')
        buf.append('Welcome to momo!')
        with open(filename, 'w') as f:
            f.write('\n'.join(buf))
        return res

    def _serve(self, args=None):
        os.chdir(self.mkdocs_dir)
        cmd = 'mkdocs'
        cmd_args = []
        if not args:
            cmd_args = ['serve']
        else:
            cmd_args.extend(args)
        run_cmd(cmd=cmd, cmd_args=cmd_args)

    def run(self, extra_args=None):
        pages = self._get_pages(self.settings.bucket.root)
        self.mkdocs_configs['pages'] = pages
        self._make_mkdocs_yml()
        self._serve(extra_args)


plugin = Mkdocs()
