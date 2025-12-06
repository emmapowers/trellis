


# Compact, inline definition
@reactComponent()
def Column(children: Elements) -> Elements:
    # language=html
    return t"""
    function Column(props: ColumnProps): React.ReactElement {
        return (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                {props.children}
            </div>
        );
    }
    """

# For something more complex, use a separate files
# This can include typescript, css, images, etc.
# As well as any external dependencies
class Column(ReactComponent):
    # Specify the source files for this component
    _sources = [
        "components/Column.tsx"
        "components/Column.css"
    ]
    # Specify any external ESM modules your component depends on
    _esModules = [
        "https://esm.sh/superAwesomeLib@1.2.3", # pull a NPM module from esm.sh
        "./vendored/mylib.js"  # local ESM module 
    ]
