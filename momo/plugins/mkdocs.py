import os
import shutil
import yaml
import glob
from momo.utils import run_cmd, mkdir_p, utf8_encode, txt_type, eval_path
from momo.plugins.base import Plugin


BASE_CONFIG_NAME = '__base__'


class Mkdocs(Plugin):
    mkdocs_configs = {
        'theme': 'readthedocs',
    }
    momo_configs = {
        'momo_root_name': 'Home',
        'momo_page_level': 1,
        'momo_attr_table': True,
        'momo_attr_css': True,
        'momo_docs_dir': None,
        'momo_docs_pathname': 'docs',
        'momo_control_attr': False,  # whether rendering control attriutes
    }

    def setup(self):
        self.root = self.settings.bucket.root
        bucket_name = self.settings.bucket.name
        base_configs = self.settings.plugins.get(
            'mkdocs', {}).get(BASE_CONFIG_NAME, {})
        configs = self.settings.plugins.get(
            'mkdocs', {}).get(bucket_name, {})
        for k in base_configs:
            if k not in configs:
                configs[k] = base_configs[k]

        # mkdocs site_name defaults to bucket name
        self.mkdocs_configs['site_name'] = bucket_name

        for k in configs:
            if not k.startswith('momo_'):
                self.mkdocs_configs[k] = configs[k]
        for k in configs:
            if k.startswith('momo_'):
                self.momo_configs[k] = configs[k]

        self.mkdocs_root_dir = os.path.join(self.settings.settings_dir,
                                            'mkdocs')
        self.mkdocs_dir = os.path.join(self.mkdocs_root_dir,
                                       bucket_name)
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

        self.root.name = self.momo_configs['momo_root_name']

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

    def _get_docs(self):
        if self.momo_configs['momo_docs_dir'] is None:
            return []
        src_momo_docs_dir = eval_path(self.momo_configs['momo_docs_dir'])
        if os.path.isdir(src_momo_docs_dir):
            markdown_paths = glob.glob(
                os.path.join(src_momo_docs_dir, '*.md'))
            momo_docs_dir = os.path.join(
                self.docs_dir, self.momo_configs['momo_docs_pathname'])
            mkdir_p(momo_docs_dir)
            docs = []
            for markdown_path in markdown_paths:
                shutil.copy(markdown_path, momo_docs_dir)
                markdown_basename = os.path.basename(markdown_path)
                doc_title = os.path.splitext(markdown_basename)[0].title()
                doc_path = os.path.join(
                    self.momo_configs['momo_docs_pathname'], markdown_basename
                )
                docs.append({doc_title: doc_path})
            return [{'Docs': docs}]

    def _get_lazy_load_size(self, elem):
        """Get lazy load size for attributes of the current element's nodes."""
        attr = elem.attrs.get('momo_lazy_load_size')
        lazy_load_size = attr.content if attr is not None else None
        if lazy_load_size is not None:
            # parse size in WIDTHxHEIGHT format (px)
            try:
                width, height = map(int, lazy_load_size.split('x'))
            except ValueError:
                Exception(
                    'Invalid "momo_lazy_load_size" value %s' % lazy_load_size)
            return (width, height)
        return lazy_load_size

    def _get_this_lazy_load_size(self, elem):
        """Get lazy load size for current element's attributes."""
        attr = elem.attrs.get('momo_this_lazy_load_size')
        this_lazy_load_size = attr.content if attr is not None else None
        if this_lazy_load_size is not None:
            # parse size in WIDTHxHEIGHT format (px)
            try:
                width, height = map(int, this_lazy_load_size.split('x'))
            except ValueError:
                Exception(
                    'Invalid "momo_this_lazy_load_size" value %s' %
                    this_lazy_load_size)
            return (width, height)
        return this_lazy_load_size

    def _make_page(self, elem):
        res = '%s.md' % os.path.join(*elem.path)
        filename = os.path.join(self.docs_dir, res)
        dirname = os.path.dirname(filename)
        if dirname:
            mkdir_p(dirname)
        kwargs = {}
        this_kwargs = {}
        lazy_load_size = self._get_lazy_load_size(elem)
        this_lazy_load_size = self._get_this_lazy_load_size(elem)
        if lazy_load_size is not None:
            kwargs['lazy_load_size'] = lazy_load_size
        if this_lazy_load_size is not None:
            this_kwargs['lazy_load_size'] = this_lazy_load_size
        buf = []
        with open(filename, 'w') as f:
            buf.append(self._make_title(elem))
            buf.append(self._make_attrs(elem, **this_kwargs))
            buf.append(self._make_nodes(elem, **kwargs))
            f.write(utf8_encode('\n'.join(buf)))
        return res

    def _make_index_page(self, elem, level):
        base = os.path.join(*elem.path) if elem.path else ''
        res = os.path.join(base, 'index.md')
        filename = os.path.join(self.docs_dir, res)
        dirname = os.path.dirname(filename)
        if dirname:
            mkdir_p(dirname)
        kwargs = {}
        lazy_load_size = self._get_lazy_load_size(elem)
        if lazy_load_size is not None:
            kwargs['lazy_load_size'] = lazy_load_size
        buf = []
        with open(filename, 'w') as f:
            buf.append(self._make_title(elem))
            buf.append(self._make_attrs(elem))
            buf.append(self._make_nodes(elem, index=True, level=level,
                                        **kwargs))
            f.write(utf8_encode('\n'.join(buf)))
        return res

    def _make_title(self, elem):
        return '# %s' % elem.name

    def _filter_control_attrs(self, attrs):
        if not self.momo_configs['momo_control_attr']:
            return filter(lambda x: not x.name.startswith('momo_'), attrs)
        return attrs

    def _make_attrs(self, elem, **kwargs):
        buf = []
        if self.momo_configs['momo_attr_css']:
            name_fmt = ('<span class="momo-attr-name '
                        'momo-attr-name-{name}">'
                        '{name}</span>')
        else:
            name_fmt = '{name}'
        if self.momo_configs['momo_attr_css']:
            content_fmt = ('<span class="momo-attr-content '
                           'momo-attr-content-{name}">'
                           '{content}</span>')
        else:
            content_fmt = '{content}'
        if self.momo_configs['momo_attr_table']:
            if elem.attr_svals:
                buf.append('')
                buf.append('|')
                buf.append('- | -')
            for attr in self._filter_control_attrs(elem.attr_svals):
                buf.append(
                    txt_type(name_fmt + ' | ' + content_fmt).format(
                        name=attr.name,
                        content=self._make_attr_content(attr, **kwargs).strip()
                    )
                )
            buf.append('')
        else:
            for attr in self._filter_control_attrs(elem.attr_svals):
                buf.append('\n')
                buf.append(
                    '- %s:%s' % (attr.name,
                                 self._make_attr_content(attr, **kwargs)))
                buf.append(
                    txt_type('- ' + name_fmt + ':' + content_fmt).format(
                        name=attr.name,
                        content=self._make_attr_content(attr, **kwargs).strip()
                    )
                )
        return '\n'.join(buf)

    def _make_attr_content(self, attr, **kwargs):
        buf = []
        if attr.has_items:
            buf.append('\n')
            for i, item in enumerate(attr.content, start=1):
                if self.momo_configs['momo_attr_table']:
                    buf.append(self._make_link(item, **kwargs))
                else:
                    buf.append('    - %s' % (self._make_link(item, **kwargs)))
        else:
            buf.append(' %s' % self._make_object(attr, **kwargs))
        if self.momo_configs['momo_attr_table']:
            if buf and buf[0] == '\n':
                buf.pop(0)
            return '<br>'.join(buf)
        else:
            return '\n'.join(buf)

    def _make_object(self, attr, **kwargs):
        name = attr.name
        content = attr.content
        if name.lower() in ('url', 'link'):
            return self._make_link(content, **kwargs)
        elif name.lower() in ('image'):
            return self._make_image(content, **kwargs)
        else:
            return self._make_link(content, **kwargs)
        return content

    def _make_link(self, content, **kwargs):
        if isinstance(content, txt_type) and content.startswith('http'):
            content = '[%s](%s)' % (content, content)
        return content

    def _make_image(self, content, **kwargs):
        res = '\n\n'
        if isinstance(content, txt_type) and content.startswith('http'):
            if 'lazy_load_size' in kwargs:
                width, height = kwargs['lazy_load_size']
                img = (
                    '<a href="{image}" title="image">'
                    '<img class="lazy" '
                    'data-original="{image}" '
                    'width="{width}px" '
                    'height="{height}px" '
                    '/></a>'
                ).format(image=content, width=width, height=height)
                res += img
            else:
                res += '[![image]({image})]({image} "image")'.format(
                    image=content)
        return res

    def _make_nodes(self, elem, index=False, level=None, **kwargs):
        buf = []
        if not index:
            for node in elem.node_svals:
                this_kwargs = dict(kwargs)  # get a fresh copy for each node
                buf.append('## %s' % (node.name))
                this_lazy_load_size = self._get_this_lazy_load_size(node)
                if this_lazy_load_size is not None:
                    this_kwargs['lazy_load_size'] = this_lazy_load_size
                buf.append(self._make_attrs(node, **this_kwargs))
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

    def _serve(self, args=None):
        os.chdir(self.mkdocs_dir)
        cmd = 'mkdocs'
        cmd_args = []
        if not args:
            cmd_args = ['serve']
        else:
            cmd_args.extend(args)
        run_cmd(cmd=cmd, cmd_args=cmd_args)

    def run(self, args=None):
        pages = self._get_pages(self.root)
        docs = self._get_docs()
        self.mkdocs_configs['pages'] = pages + docs
        self._make_mkdocs_yml()
        self._serve(args)


plugin = Mkdocs()
