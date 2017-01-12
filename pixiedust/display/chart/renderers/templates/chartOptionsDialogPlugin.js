// don't remove this comment
mpld3.register_plugin("dialog", DialogPlugin);
DialogPlugin.prototype = Object.create(mpld3.Plugin.prototype);
DialogPlugin.prototype.constructor = DialogPlugin;
DialogPlugin.prototype.requiredProps = ["handlerId"];    
function DialogPlugin(fig, props) {
    mpld3.Plugin.call(this, fig, props);
    var DialogPluginButton = mpld3.ButtonFactory({
        buttonID: "DialogPlugin",
        sticky: false,
        onActivate: function() {
            {%include resModule + ":chartOptions.dialog"%}
        },
        icon: function() {
            return mpld3.icons["brush"];
        }
    });
    this.fig.buttons.push(DialogPluginButton);
}