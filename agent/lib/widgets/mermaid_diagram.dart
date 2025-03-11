import 'dart:html' as html;
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:mermaid/mermaid.dart' as mermaid;

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
    _initializeMermaid();
  }

  void _initializeMermaid() {
    if (_initialized) return;
    _initialized = true;

    // Register view factory
    ui_web.platformViewRegistry.registerViewFactory(
      _viewType,
      (int viewId) {
        // Create the main container
        final host = html.DivElement()
          ..style.width = '${widget.width}px'
          ..style.height = '${widget.height}px'
          ..style.overflow = 'hidden'
          ..style.backgroundColor = 'transparent';

        // Add custom styles for Mermaid diagrams
        final styleElement = html.StyleElement()
          ..text = '''
            .mermaid {
              display: flex;
              justify-content: center;
              align-items: center;
              width: 100%;
              height: 100%;
              background-color: transparent;
            }
            .mermaid svg {
              width: 100% !important;
              height: 100% !important;
              max-width: none !important;
              max-height: none !important;
            }
            .mermaid .label {
              font-family: 'Arial', sans-serif;
              font-size: 16px !important;
              fill: white !important;
              color: white !important;
            }
            .mermaid .node rect,
            .mermaid .node circle,
            .mermaid .node ellipse,
            .mermaid .node polygon,
            .mermaid .node path {
              fill: #2A2A2A !important;
              stroke: #4A4A4A !important;
            }
            .mermaid .edgePath .path {
              stroke: #7A7A7A !important;
              stroke-width: 2px !important;
            }
            .mermaid .arrowheadPath {
              fill: #7A7A7A !important;
              stroke: none !important;
            }
            .mermaid .messageText,
            .mermaid .noteText {
              fill: white !important;
              stroke: none !important;
              font-size: 14px !important;
            }
            .mermaid .actor {
              fill: #2A2A2A !important;
              stroke: #4A4A4A !important;
            }
            .mermaid text.actor {
              fill: white !important;
              stroke: none !important;
            }
          ''';

        host.append(styleElement);

        // Add the mermaid diagram
        host.appendHtml('''
          <pre class="mermaid">
${widget.diagramCode}
          </pre>
        ''',
            validator: html.NodeValidatorBuilder()
              ..allowElement('pre', attributes: ['class'])
              ..allowElement('style')
              ..allowHtml5());

        // Initialize mermaid with custom config
        html.ScriptElement script = html.ScriptElement()
          ..text = '''
            mermaid.initialize({
              startOnLoad: true,
              theme: 'dark',
              securityLevel: 'loose',
              logLevel: 'error',
              sequence: {
                actorMargin: 50,
                messageMargin: 40,
                width: ${widget.width * 0.9},
                height: ${widget.height * 0.9},
                boxMargin: 10,
                mirrorActors: false,
                bottomMarginAdj: 10,
                useMaxWidth: false
              },
              flowchart: {
                nodeSpacing: 50,
                rankSpacing: 50,
                curve: 'basis',
                useMaxWidth: false
              }
            });
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
          ''';

        host.append(script);

        return host;
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: widget.width,
      height: widget.height,
      decoration: BoxDecoration(
        color: Colors.transparent,
      ),
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
