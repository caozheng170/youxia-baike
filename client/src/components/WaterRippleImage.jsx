import React, {
  useRef,
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
  useState,
} from 'react';
import './WaterRippleImage.css';

const MAX_RIPPLES = 8;

const VERTEX_SHADER = `
  attribute vec2 a_position;
  attribute vec2 a_texCoord;
  varying vec2 v_texCoord;
  void main() {
    v_texCoord = a_texCoord;
    gl_Position = vec4(a_position, 0.0, 1.0);
  }
`;

const FRAGMENT_SHADER = `
  precision mediump float;
  uniform sampler2D u_texture;
  uniform vec2 u_ripples[${MAX_RIPPLES}];
  uniform float u_times[${MAX_RIPPLES}];
  uniform int u_count;
  uniform float u_boost;
  varying vec2 v_texCoord;

  vec2 rippleOffset(vec2 uv, vec2 origin, float t) {
    vec2 delta = uv - origin;
    float dist = length(delta);
    if (dist < 0.0005) return vec2(0.0);
    vec2 dir = delta / dist;
    float rings = sin(dist * 52.0 - t * 11.0);
    float envelope = exp(-dist * 4.2) * exp(-t * (0.9 + u_boost * -0.55));
    float amp = 0.042 + u_boost * 0.022;
    return dir * rings * envelope * amp;
  }

  void main() {
    vec2 uv = v_texCoord;
    vec2 offset = vec2(0.0);
    for (int i = 0; i < ${MAX_RIPPLES}; i++) {
      if (i >= u_count) continue;
      offset += rippleOffset(uv, u_ripples[i], u_times[i]);
    }
    gl_FragColor = texture2D(u_texture, clamp(uv + offset, 0.001, 0.999));
  }
`;

function createShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

function createProgram(gl, vs, fs) {
  const program = gl.createProgram();
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(program));
    return null;
  }
  return program;
}

/**
 * Image as a water surface — click disturbs the image with real UV warping.
 */
const WaterRippleImage = forwardRef(function WaterRippleImage(
  {
    src,
    alt,
    className = '',
    disabled = false,
    sustainRipple = false,
    onClick,
  },
  ref
) {
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const fallbackRef = useRef(null);
  const glRef = useRef(null);
  const programRef = useRef(null);
  const textureRef = useRef(null);
  const ripplesRef = useRef([]);
  const rafRef = useRef(null);
  const boostRef = useRef(0);
  const [useFallback, setUseFallback] = useState(false);
  const [aspectRatio, setAspectRatio] = useState('16 / 9');

  useImperativeHandle(ref, () => ({
    getBoundingClientRect: () =>
      (wrapRef.current || fallbackRef.current)?.getBoundingClientRect(),
  }));

  const addRipple = useCallback((nx, ny) => {
    const now = performance.now();
    ripplesRef.current = [
      ...ripplesRef.current.slice(-(MAX_RIPPLES - 1)),
      { x: nx, y: ny, start: now },
    ];
  }, []);

  const loadTexture = useCallback((gl, image) => {
    if (textureRef.current) {
      gl.deleteTexture(textureRef.current);
    }
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    textureRef.current = tex;
    if (image.naturalWidth && image.naturalHeight) {
      setAspectRatio(`${image.naturalWidth} / ${image.naturalHeight}`);
    }
  }, []);

  const resizeCanvas = useCallback(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    const gl = glRef.current;
    if (!wrap || !canvas || !gl) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    if (w === 0 || h === 0) return;

    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
  }, []);

  const draw = useCallback(() => {
    const gl = glRef.current;
    const program = programRef.current;
    if (!gl || !program || !textureRef.current) return;

    const now = performance.now();
    boostRef.current = sustainRipple ? 1 : 0;

    ripplesRef.current = ripplesRef.current.filter((r) => (now - r.start) / 1000 < 6);

    if (sustainRipple && ripplesRef.current.length > 0) {
      const last = ripplesRef.current[ripplesRef.current.length - 1];
      if (now - last.start > 1400) {
        ripplesRef.current.push({ x: last.x, y: last.y, start: now });
        if (ripplesRef.current.length > MAX_RIPPLES) {
          ripplesRef.current = ripplesRef.current.slice(-MAX_RIPPLES);
        }
      }
    }

    const count = ripplesRef.current.length;
    const positions = new Float32Array(MAX_RIPPLES * 2);
    const times = new Float32Array(MAX_RIPPLES);
    ripplesRef.current.forEach((r, i) => {
      positions[i * 2] = r.x;
      positions[i * 2 + 1] = 1 - r.y;
      times[i] = (now - r.start) / 1000;
    });

    gl.useProgram(program);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textureRef.current);

    gl.uniform1i(gl.getUniformLocation(program, 'u_texture'), 0);
    gl.uniform2fv(gl.getUniformLocation(program, 'u_ripples'), positions);
    gl.uniform1fv(gl.getUniformLocation(program, 'u_times'), times);
    gl.uniform1i(gl.getUniformLocation(program, 'u_count'), count);
    gl.uniform1f(gl.getUniformLocation(program, 'u_boost'), boostRef.current);

    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    const stillActive =
      count > 0 && ripplesRef.current.some((r) => (now - r.start) / 1000 < 5.5);
    if (stillActive || sustainRipple) {
      rafRef.current = requestAnimationFrame(draw);
    } else {
      rafRef.current = null;
    }
  }, [sustainRipple]);

  const startLoop = useCallback(() => {
    if (!rafRef.current) {
      rafRef.current = requestAnimationFrame(draw);
    }
  }, [draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || useFallback) return;

    const gl = canvas.getContext('webgl', { alpha: false, antialias: false });
    if (!gl) {
      setUseFallback(true);
      return;
    }

    const vs = createShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
    const fs = createShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    const program = createProgram(gl, vs, fs);
    if (!program) {
      setUseFallback(true);
      return;
    }

    const posBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
      gl.STATIC_DRAW
    );
    const posLoc = gl.getAttribLocation(program, 'a_position');
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    const texBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, texBuf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([0, 1, 1, 1, 0, 0, 1, 0]),
      gl.STATIC_DRAW
    );
    const texLoc = gl.getAttribLocation(program, 'a_texCoord');
    gl.enableVertexAttribArray(texLoc);
    gl.vertexAttribPointer(texLoc, 2, gl.FLOAT, false, 0, 0);

    glRef.current = gl;
    programRef.current = program;

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [useFallback]);

  useEffect(() => {
    if (!src || useFallback) return;

    const img = new Image();
    if (!src.startsWith('data:')) {
      img.crossOrigin = 'anonymous';
    }
    img.onload = () => {
      const gl = glRef.current;
      if (!gl) return;
      loadTexture(gl, img);
      requestAnimationFrame(() => {
        resizeCanvas();
        draw();
      });
    };
    img.onerror = () => setUseFallback(true);
    img.src = src;
  }, [src, useFallback, loadTexture, resizeCanvas, draw]);

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap || useFallback) return;
    const ro = new ResizeObserver(() => {
      resizeCanvas();
      draw();
    });
    ro.observe(wrap);
    return () => ro.disconnect();
  }, [useFallback, resizeCanvas, draw]);

  useEffect(() => {
    if (sustainRipple && !useFallback) startLoop();
  }, [sustainRipple, useFallback, startLoop]);

  const handleClick = (e) => {
    if (disabled) return;
    const rect = (wrapRef.current || fallbackRef.current)?.getBoundingClientRect();
    if (!rect) return;
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;
    if (!useFallback) {
      addRipple(nx, ny);
      startLoop();
    }
    onClick?.(e, nx, ny);
  };

  if (useFallback) {
    return (
      <img
        ref={fallbackRef}
        src={src}
        alt={alt}
        className={className}
        onClick={handleClick}
        draggable={false}
      />
    );
  }

  return (
    <div
      ref={wrapRef}
      className={`water-ripple-image ${disabled ? 'disabled' : ''} ${className}`}
      style={{ aspectRatio }}
      onClick={handleClick}
      role="img"
      aria-label={alt}
    >
      <canvas ref={canvasRef} className="water-ripple-image__canvas" />
    </div>
  );
});

export default WaterRippleImage;
