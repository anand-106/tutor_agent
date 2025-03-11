import 'dart:html' as html;
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';

class MermaidDiagram extends StatefulWidget {
  final String diagramCode;
  final double width;
  final double height;

  const MermaidDiagram({
    Key? key,
    required this.diagramCode,
    this.width = 600,
    this.height = 400,
  }) : super(key: key);

  @override
  State<MermaidDiagram> createState() => _MermaidDiagramState();
}

class _MermaidDiagramState extends State<MermaidDiagram> {
  late final String _viewType;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _viewType = 'mermaid-${DateTime.now().millisecondsSinceEpoch}';
    print('MermaidDiagram initialized with viewType: $_viewType');
    _initializeMermaid();
  }

  void _initializeMermaid() {
    if (_initialized) return;
    _initialized = true;

    print('Starting Mermaid initialization...');

    // Register view factory
    ui_web.platformViewRegistry.registerViewFactory(_viewType, (int viewId) {
      print('Creating view for Mermaid diagram...');
      print('ViewId: $viewId');

      // Ensure the diagram code starts with the correct syntax
      String formattedCode = widget.diagramCode.trim();
      if (!formattedCode.startsWith('classDiagram') &&
          !formattedCode.startsWith('graph') &&
          !formattedCode.startsWith('sequenceDiagram')) {
        if (formattedCode.contains('class ')) {
          formattedCode = 'classDiagram\n' + formattedCode;
        } else {
          formattedCode = 'graph TD\n' + formattedCode;
        }
      }

      print('Formatted diagram code: $formattedCode');

      final containerId = 'mermaid-container-$viewId';
      final diagramId = 'mermaid-diagram-$viewId';

      // Create container element with fixed size
      final container = html.DivElement()
        ..id = containerId
        ..style.width = '${widget.width}px'
        ..style.height = '${widget.height}px'
        ..style.backgroundColor = 'transparent'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..style.overflow = 'hidden'
        ..style.position = 'relative';

      // Create diagram element with specific styling
      final diagramElement = html.DivElement()
        ..id = diagramId
        ..className = 'mermaid'
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..text = formattedCode;

      container.children.add(diagramElement);

      print('Created container with ID: $containerId');

      // Add script to render diagram
      html.ScriptElement script = html.ScriptElement()
        ..text = '''
          function initAndRenderMermaid() {
            if (typeof mermaid === 'undefined') {
              console.error('Mermaid not found, retrying in 100ms...');
              setTimeout(initAndRenderMermaid, 100);
              return;
            }

            try {
              console.log('Initializing Mermaid for $diagramId');
              mermaid.initialize({
                startOnLoad: true,
                theme: 'dark',
                securityLevel: 'loose',
                logLevel: 'debug',
                flowchart: {
                  htmlLabels: true,
                  curve: 'basis',
                  useMaxWidth: true,
                  padding: 20
                },
                class: {
                  useMaxWidth: true
                },
                sequence: {
                  useMaxWidth: true,
                  showSequenceNumbers: false,
                  wrap: false,
                  width: ${widget.width - 40}, // Account for padding
                  height: ${widget.height - 40}
                }
              });

              console.log('Running Mermaid render for $diagramId');
              mermaid.run({
                querySelector: '#$diagramId',
                suppressErrors: false
              }).then(() => {
                console.log('Mermaid render successful for $diagramId');
                const svg = document.querySelector('#$diagramId svg');
                if (svg) {
                  svg.style.maxWidth = '100%';
                  svg.style.maxHeight = '100%';
                  svg.style.width = 'auto';
                  svg.style.height = 'auto';
                  svg.style.backgroundColor = 'transparent';
                  svg.style.display = 'block';
                  svg.style.margin = 'auto';
                  
                  // Ensure SVG fits within container
                  const bbox = svg.getBBox();
                  const scale = Math.min(
                    (${widget.width} - 40) / bbox.width,
                    (${widget.height} - 40) / bbox.height
                  );
                  
                  if (scale < 1) {
                    svg.style.transform = `scale(\${scale})`;
                  }
                }
              }).catch((error) => {
                console.error('Mermaid render error:', error);
              });
            } catch (error) {
              console.error('Error in mermaid initialization/render:', error);
            }
          }

          // Start the initialization/render process
          initAndRenderMermaid();
        ''';

      container.children.add(script);
      return container;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: widget.width,
      height: widget.height,
      decoration: BoxDecoration(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      clipBehavior: Clip.hardEdge,
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
