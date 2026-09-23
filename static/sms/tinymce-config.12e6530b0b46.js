// tinymce-config.js

// Initialize TinyMCE with external integration for MathType
tinymce.init({
    selector: 'textarea', // Use appropriate selector for your textarea
    plugins: 'tiny_mce_wiris', // Include MathType plugin via external integration
    toolbar: 'undo redo | bold italic | tiny_mce_wiris_formulaEditor | tiny_mce_wiris_formulaEditorChemistry', // Add MathType buttons to the toolbar
    external_plugins: {
      'tiny_mce_wiris': 'https://www.wiris.net/demo/plugins/tiny_mce/plugin.js' // Specify the URL of the MathType plugin
    }
  });
  