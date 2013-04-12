<%def name="render_quote(quote)">
    <pre>${quote.content}</pre>
    <p>
        kudos ${quote.poster.name}
        % if quote.comment:
            — “${quote.comment}”
        % endif
    </p>
    <p>${quote.timestamp}</p>
</%def>