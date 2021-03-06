import pygments
import pygments.formatters
import pygments.lexers
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from spline.models import session
from spline_pastebin.models import Paste


@view_config(route_name='pastebin.new', renderer='spline_pastebin:templates/new.mako')
def home(request):
    # Fetch all the lexers.  We only need a map of alias => name to build the
    # form, so grab those.  Using a set helps when Pygments has duplicate
    # lexers (that claim to own different file or MIME types), which is a thing
    # that happens apparently.
    lexerset = set()
    for name, aliases, filetypes, mimetypes in pygments.lexers.get_all_lexers():
        lexerset.add((name, aliases[0]))

    # Sort by name
    lexers = list(lexerset)
    lexers.sort(key=lambda lexer: lexer[0].lower())

    return dict(
        #guessed_name=ipmap.get(request.remote_addr, ''),
        lexers=lexers,
    )

@view_config(route_name='pastebin.new', request_method='POST')
def do_paste(request):
    syntax = request.POST['syntax']
    if syntax == '[none]':
        syntax = ''
    elif syntax == '[auto]':
        lexer = pygments.lexers.guess_lexer(request.POST['content'])
        syntax = lexer.aliases[0]
    elif syntax.startswith('['):
        raise ValueError

    content = request.POST['content']
    lines = content.count('\n')
    if content[-1] != '\n':
        lines += 1

    paste = Paste(
        author=request.user,
        title=request.POST.get('title', ''),
        syntax=syntax,
        content=content,
        size=len(content),
        lines=lines,
    )
    session.add(paste)
    session.flush()

    return HTTPSeeOther(location=request.route_url('pastebin.view', id=paste.id))


@view_config(route_name='pastebin.list', renderer='spline_pastebin:templates/list.mako')
def list_paste(request):
    pastes = session.query(Paste) \
        .order_by(Paste.id.desc()) \
        .limit(20)

    return dict(pastes=pastes)


@view_config(route_name='pastebin.view', renderer='spline_pastebin:templates/view.mako')
def view(request):
    paste = session.query(Paste) \
        .filter(Paste.id == request.matchdict['id']) \
        .one()

    if paste.syntax != '':
        lexer = pygments.lexers.get_lexer_by_name(paste.syntax)
    else:
        lexer = pygments.lexers.TextLexer()
    pretty_content = pygments.highlight(paste.content, lexer, pygments.formatters.HtmlFormatter())

    return dict(
        paste=paste,
        pretty_content=pretty_content,
    )


