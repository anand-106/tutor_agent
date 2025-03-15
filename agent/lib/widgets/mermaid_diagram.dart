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

      // Clean up the code by removing problematic characters and fixing syntax
      String formattedCode = widget.diagramCode.trim();

      // Ensure proper diagram type prefix
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

      // Create container with unique ID
      final container = html.DivElement()
        ..id = _viewType
        ..style.width = '${widget.width}px'
        ..style.height = '${widget.height}px'
        ..style.backgroundColor = 'transparent'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..style.overflow = 'hidden'
        ..style.position = 'relative';

      // Create diagram element
      final diagramElement = html.DivElement()
        ..className = 'mermaid'
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.display = 'flex'
        ..style.justifyContent = 'center'
        ..style.alignItems = 'center'
        ..text = formattedCode;

      container.children.add(diagramElement);

      // Add script to render diagram
      final script = html.ScriptElement()
        ..text = '''
          (function() {
            function renderDiagram() {
              if (typeof mermaid === 'undefined') {
                console.log('Waiting for Mermaid to load...');
                setTimeout(renderDiagram, 100);
                return;
              }

              try {
                console.log('Rendering diagram for ${_viewType}');
                mermaid.run({
                  querySelector: '#${_viewType} .mermaid',
                  suppressErrors: false
                }).then(() => {
                  console.log('Render successful for ${_viewType}');
                  const svg = document.querySelector('#${_viewType} svg');
                  if (svg) {
                    svg.style.maxWidth = '100%';
                    svg.style.maxHeight = '100%';
                    svg.style.width = 'auto';
                    svg.style.height = 'auto';
                    svg.style.backgroundColor = 'transparent';
                    
                    // Calculate and set viewBox
                    const bbox = svg.getBBox();
                    const padding = 20;
                    svg.setAttribute('viewBox', 
                      `\${bbox.x - padding} \${bbox.y - padding} \${bbox.width + padding * 2} \${bbox.height + padding * 2}`
                    );
                    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
                  }
                }).catch(error => {
                  console.error('Render error:', error);
                  const errorDiv = document.createElement('div');
                  errorDiv.style.color = '#ff6b6b';
                  errorDiv.style.padding = '16px';
                  errorDiv.innerHTML = `Error rendering diagram: \${error.message || 'Unknown error'}`;
                  document.querySelector('#${_viewType}').appendChild(errorDiv);
                });
              } catch (error) {
                console.error('Error in render:', error);
              }
            }
            renderDiagram();
          })();
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
