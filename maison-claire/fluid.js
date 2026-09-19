/* Maison Claire - brand-tinted WebGL fluid.
   Trimmed adaptation of Pavel Dobryakov's WebGL-Fluid-Simulation (MIT).
   Full-screen intro burst that settles into a subtle layer behind the hero. */
(function () {
  var canvas = document.querySelector('.fluid-canvas');
  if (!canvas) return;

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var splash = document.getElementById('fluidSplash');
  if (reduce) {                       // accessibility: no motion, no splash
    if (splash && splash.parentNode) splash.parentNode.removeChild(splash);
    canvas.style.display = 'none';
    return;
  }

  var config = {
    SIM_RESOLUTION: 128,
    DYE_RESOLUTION: 640,
    DENSITY_DISSIPATION: 1.75,
    VELOCITY_DISSIPATION: 0.35,
    PRESSURE: 0.8,
    PRESSURE_ITERATIONS: 20,
    CURL: 18,
    SPLAT_RADIUS: 0.18,
    SPLAT_FORCE: 6000
  };

  // Brand palette (navy/gold/cream/soft teal/rose), kept gentle.
  var PALETTE = [
    [0.85, 0.68, 0.38],  // gold
    [0.94, 0.90, 0.80],  // cream
    [0.34, 0.53, 0.64],  // soft teal-blue
    [0.80, 0.60, 0.50],  // warm rose
    [0.55, 0.70, 0.80]   // sky
  ];

  var gl, ext;
  (function getContext() {
    var params = { alpha: true, depth: false, stencil: false, antialias: false, preserveDrawingBuffer: false };
    gl = canvas.getContext('webgl2', params);
    var isWebGL2 = !!gl;
    if (!isWebGL2) gl = canvas.getContext('webgl', params) || canvas.getContext('experimental-webgl', params);
    if (!gl) { canvas.style.display = 'none'; return; }
    var halfFloat, supportLinear;
    if (isWebGL2) {
      gl.getExtension('EXT_color_buffer_float');
      supportLinear = gl.getExtension('OES_texture_float_linear');
    } else {
      halfFloat = gl.getExtension('OES_texture_half_float');
      supportLinear = gl.getExtension('OES_texture_half_float_linear');
    }
    var halfFloatTexType = isWebGL2 ? gl.HALF_FLOAT : (halfFloat && halfFloat.HALF_FLOAT_OES);
    var formatRGBA, formatRG, formatR;
    if (isWebGL2) {
      formatRGBA = getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, halfFloatTexType);
      formatRG = getSupportedFormat(gl, gl.RG16F, gl.RG, halfFloatTexType);
      formatR = getSupportedFormat(gl, gl.R16F, gl.RED, halfFloatTexType);
    } else {
      formatRGBA = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType);
      formatRG = formatRGBA;
      formatR = formatRGBA;
    }
    ext = { formatRGBA: formatRGBA, formatRG: formatRG, formatR: formatR, halfFloatTexType: halfFloatTexType, supportLinearFiltering: supportLinear };
    ext.isWebGL2 = isWebGL2;
    if (!formatRGBA) { canvas.style.display = 'none'; gl = null; }
  })();
  if (!gl) { if (splash && splash.parentNode) splash.parentNode.removeChild(splash); return; }

  function getSupportedFormat(gl, internalFormat, format, type) {
    if (!supportRenderTextureFormat(gl, internalFormat, format, type)) {
      if (ext && ext.isWebGL2) {
        switch (internalFormat) {
          case gl.R16F: return getSupportedFormat(gl, gl.RG16F, gl.RG, type);
          case gl.RG16F: return getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, type);
        }
      }
      return null;
    }
    return { internalFormat: internalFormat, format: format };
  }
  function supportRenderTextureFormat(gl, internalFormat, format, type) {
    var texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, 4, 4, 0, format, type, null);
    var fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
    var status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    return status === gl.FRAMEBUFFER_COMPLETE;
  }

  function compileShader(type, source) {
    var shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) console.warn(gl.getShaderInfoLog(shader));
    return shader;
  }
  function createProgram(vs, fs) {
    var program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) console.warn(gl.getProgramInfoLog(program));
    return program;
  }
  function getUniforms(program) {
    var uniforms = {};
    var count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < count; i++) {
      var name = gl.getActiveUniform(program, i).name;
      uniforms[name] = gl.getUniformLocation(program, name);
    }
    return uniforms;
  }
  function Program(vs, fs) {
    this.program = createProgram(vs, fs);
    this.uniforms = getUniforms(this.program);
    this.bind = function () { gl.useProgram(this.program); };
  }

  var baseVertex = compileShader(gl.VERTEX_SHADER,
    'precision highp float;attribute vec2 aPosition;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform vec2 texelSize;' +
    'void main(){vUv=aPosition*0.5+0.5;vL=vUv-vec2(texelSize.x,0.0);vR=vUv+vec2(texelSize.x,0.0);vT=vUv+vec2(0.0,texelSize.y);vB=vUv-vec2(0.0,texelSize.y);gl_Position=vec4(aPosition,0.0,1.0);}');

  var copyShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;uniform sampler2D uTexture;void main(){gl_FragColor=texture2D(uTexture,vUv);}');

  var clearShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;uniform sampler2D uTexture;uniform float value;void main(){gl_FragColor=value*texture2D(uTexture,vUv);}');

  var displayShader = compileShader(gl.FRAGMENT_SHADER,
    'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uTexture;' +
    'void main(){vec3 c=texture2D(uTexture,vUv).rgb;float a=max(c.r,max(c.g,c.b));gl_FragColor=vec4(c,a);}');

  var splatShader = compileShader(gl.FRAGMENT_SHADER,
    'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uTarget;uniform float aspectRatio;uniform vec3 color;uniform vec2 point;uniform float radius;' +
    'void main(){vec2 p=vUv-point.xy;p.x*=aspectRatio;vec3 splat=exp(-dot(p,p)/radius)*color;vec3 base=texture2D(uTarget,vUv).xyz;gl_FragColor=vec4(base+splat,1.0);}');

  var advectionShader = compileShader(gl.FRAGMENT_SHADER,
    'precision highp float;precision highp sampler2D;varying vec2 vUv;uniform sampler2D uVelocity;uniform sampler2D uSource;uniform vec2 texelSize;uniform vec2 dyeTexelSize;uniform float dt;uniform float dissipation;' +
    'vec4 bilerp(sampler2D sam,vec2 uv,vec2 tsize){vec2 st=uv/tsize-0.5;vec2 iuv=floor(st);vec2 fuv=fract(st);vec4 a=texture2D(sam,(iuv+vec2(0.5,0.5))*tsize);vec4 b=texture2D(sam,(iuv+vec2(1.5,0.5))*tsize);vec4 c=texture2D(sam,(iuv+vec2(0.5,1.5))*tsize);vec4 d=texture2D(sam,(iuv+vec2(1.5,1.5))*tsize);return mix(mix(a,b,fuv.x),mix(c,d,fuv.x),fuv.y);}' +
    'void main(){vec2 coord=vUv-dt*bilerp(uVelocity,vUv,texelSize).xy*texelSize;vec4 result=bilerp(uSource,coord,dyeTexelSize);float decay=1.0+dissipation*dt;gl_FragColor=result/decay;}');

  var divergenceShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uVelocity;' +
    'void main(){float L=texture2D(uVelocity,vL).x;float R=texture2D(uVelocity,vR).x;float T=texture2D(uVelocity,vT).y;float B=texture2D(uVelocity,vB).y;vec2 C=texture2D(uVelocity,vUv).xy;if(vL.x<0.0)L=-C.x;if(vR.x>1.0)R=-C.x;if(vT.y>1.0)T=-C.y;if(vB.y<0.0)B=-C.y;float div=0.5*(R-L+T-B);gl_FragColor=vec4(div,0.0,0.0,1.0);}');

  var curlShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uVelocity;' +
    'void main(){float L=texture2D(uVelocity,vL).y;float R=texture2D(uVelocity,vR).y;float T=texture2D(uVelocity,vT).x;float B=texture2D(uVelocity,vB).x;float vorticity=R-L-T+B;gl_FragColor=vec4(0.5*vorticity,0.0,0.0,1.0);}');

  var vorticityShader = compileShader(gl.FRAGMENT_SHADER,
    'precision highp float;precision highp sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uVelocity;uniform sampler2D uCurl;uniform float curl;uniform float dt;' +
    'void main(){float L=texture2D(uCurl,vL).x;float R=texture2D(uCurl,vR).x;float T=texture2D(uCurl,vT).x;float B=texture2D(uCurl,vB).x;float C=texture2D(uCurl,vUv).x;vec2 force=0.5*vec2(abs(T)-abs(B),abs(R)-abs(L));force/=length(force)+0.0001;force*=curl*C;force.y*=-1.0;vec2 velocity=texture2D(uVelocity,vUv).xy;velocity+=force*dt;velocity=min(max(velocity,-1000.0),1000.0);gl_FragColor=vec4(velocity,0.0,1.0);}');

  var pressureShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uPressure;uniform sampler2D uDivergence;' +
    'void main(){float L=texture2D(uPressure,vL).x;float R=texture2D(uPressure,vR).x;float T=texture2D(uPressure,vT).x;float B=texture2D(uPressure,vB).x;float divergence=texture2D(uDivergence,vUv).x;float pressure=(L+R+B+T-divergence)*0.25;gl_FragColor=vec4(pressure,0.0,0.0,1.0);}');

  var gradientSubtractShader = compileShader(gl.FRAGMENT_SHADER,
    'precision mediump float;precision mediump sampler2D;varying vec2 vUv;varying vec2 vL;varying vec2 vR;varying vec2 vT;varying vec2 vB;uniform sampler2D uPressure;uniform sampler2D uVelocity;' +
    'void main(){float L=texture2D(uPressure,vL).x;float R=texture2D(uPressure,vR).x;float T=texture2D(uPressure,vT).x;float B=texture2D(uPressure,vB).x;vec2 velocity=texture2D(uVelocity,vUv).xy;velocity.xy-=vec2(R-L,T-B);gl_FragColor=vec4(velocity,0.0,1.0);}');

  var copyProgram = new Program(baseVertex, copyShader);
  var clearProgram = new Program(baseVertex, clearShader);
  var splatProgram = new Program(baseVertex, splatShader);
  var advectionProgram = new Program(baseVertex, advectionShader);
  var divergenceProgram = new Program(baseVertex, divergenceShader);
  var curlProgram = new Program(baseVertex, curlShader);
  var vorticityProgram = new Program(baseVertex, vorticityShader);
  var pressureProgram = new Program(baseVertex, pressureShader);
  var gradienSubtractProgram = new Program(baseVertex, gradientSubtractShader);
  var displayProgram = new Program(baseVertex, displayShader);

  var blit = (function () {
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, -1, 1, 1, 1, 1, -1]), gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array([0, 1, 2, 0, 2, 3]), gl.STATIC_DRAW);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(0);
    return function (target) {
      if (target == null) { gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight); gl.bindFramebuffer(gl.FRAMEBUFFER, null); }
      else { gl.viewport(0, 0, target.width, target.height); gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo); }
      gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
    };
  })();

  var dye, velocity, divergenceFBO, curlFBO, pressureFBO;

  function createFBO(w, h, internalFormat, format, type, param) {
    gl.activeTexture(gl.TEXTURE0);
    var texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, param);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, param);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, w, h, 0, format, type, null);
    var fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
    gl.viewport(0, 0, w, h);
    gl.clear(gl.COLOR_BUFFER_BIT);
    var texelX = 1.0 / w, texelY = 1.0 / h;
    return {
      texture: texture, fbo: fbo, width: w, height: h, texelSizeX: texelX, texelSizeY: texelY,
      attach: function (id) { gl.activeTexture(gl.TEXTURE0 + id); gl.bindTexture(gl.TEXTURE_2D, texture); return id; }
    };
  }
  function createDoubleFBO(w, h, internalFormat, format, type, param) {
    var fbo1 = createFBO(w, h, internalFormat, format, type, param);
    var fbo2 = createFBO(w, h, internalFormat, format, type, param);
    return {
      width: w, height: h, texelSizeX: fbo1.texelSizeX, texelSizeY: fbo1.texelSizeY,
      get read() { return fbo1; }, set read(v) { fbo1 = v; },
      get write() { return fbo2; }, set write(v) { fbo2 = v; },
      swap: function () { var t = fbo1; fbo1 = fbo2; fbo2 = t; }
    };
  }

  function getResolution(resolution) {
    var aspectRatio = gl.drawingBufferWidth / gl.drawingBufferHeight;
    if (aspectRatio < 1) aspectRatio = 1.0 / aspectRatio;
    var min = Math.round(resolution);
    var max = Math.round(resolution * aspectRatio);
    if (gl.drawingBufferWidth > gl.drawingBufferHeight) return { width: max, height: min };
    return { width: min, height: max };
  }

  function initFramebuffers() {
    var simRes = getResolution(config.SIM_RESOLUTION);
    var dyeRes = getResolution(config.DYE_RESOLUTION);
    var texType = ext.halfFloatTexType;
    var rgba = ext.formatRGBA, rg = ext.formatRG, r = ext.formatR;
    var filtering = ext.supportLinearFiltering ? gl.LINEAR : gl.NEAREST;
    gl.disable(gl.BLEND);
    dye = createDoubleFBO(dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering);
    velocity = createDoubleFBO(simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering);
    divergenceFBO = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
    curlFBO = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
    pressureFBO = createDoubleFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST);
  }

  function resizeCanvas() {
    var w = Math.floor(canvas.clientWidth * (window.devicePixelRatio > 1.5 ? 1.25 : window.devicePixelRatio || 1));
    var h = Math.floor(canvas.clientHeight * (window.devicePixelRatio > 1.5 ? 1.25 : window.devicePixelRatio || 1));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; return true; }
    return false;
  }

  var pointers = [{ id: -1, texcoordX: 0, texcoordY: 0, prevTexcoordX: 0, prevTexcoordY: 0, deltaX: 0, deltaY: 0, down: false, moved: false, color: [0.2, 0.2, 0.2] }];

  function pick() { return PALETTE[Math.floor(Math.random() * PALETTE.length)]; }
  function colorScaled(c, s) { return { r: c[0] * s, g: c[1] * s, b: c[2] * s }; }

  function correctRadius(radius) {
    var aspectRatio = canvas.width / canvas.height;
    if (aspectRatio > 1) radius *= aspectRatio;
    return radius;
  }
  function splat(x, y, dx, dy, color) {
    splatProgram.bind();
    gl.uniform1i(splatProgram.uniforms.uTarget, velocity.read.attach(0));
    gl.uniform1f(splatProgram.uniforms.aspectRatio, canvas.width / canvas.height);
    gl.uniform2f(splatProgram.uniforms.point, x, y);
    gl.uniform3f(splatProgram.uniforms.color, dx, dy, 0.0);
    gl.uniform1f(splatProgram.uniforms.radius, correctRadius(config.SPLAT_RADIUS / 100.0));
    blit(velocity.write); velocity.swap();
    gl.uniform1i(splatProgram.uniforms.uTarget, dye.read.attach(0));
    gl.uniform3f(splatProgram.uniforms.color, color.r, color.g, color.b);
    blit(dye.write); dye.swap();
  }
  function splatPointer(p, boost) {
    var dx = p.deltaX * config.SPLAT_FORCE, dy = p.deltaY * config.SPLAT_FORCE;
    splat(p.texcoordX, p.texcoordY, dx, dy, colorScaled(p.color, 0.13 * (boost || 1)));
  }
  function randomSplat(intensity) {
    var c = pick();
    var x = Math.random(), y = Math.random();
    var dx = 900 * (Math.random() - 0.5), dy = 900 * (Math.random() - 0.5);
    splat(x, y, dx, dy, colorScaled(c, intensity));
  }
  // A single cohesive bloom from the centre - reads as one burst, not scattered dots.
  function centerBurst(strength) {
    strength = strength || 1;
    var aspect = canvas.width / canvas.height;
    var n = 9;
    for (var i = 0; i < n; i++) {
      var ang = (i / n) * Math.PI * 2 + Math.random() * 0.25;
      var r = 0.03 + Math.random() * 0.04;
      var x = 0.5 + Math.cos(ang) * r / (aspect > 1 ? aspect : 1);
      var y = 0.5 + Math.sin(ang) * r;
      var speed = (620 + Math.random() * 420) * strength;
      splat(x, y, Math.cos(ang) * speed, Math.sin(ang) * speed, colorScaled(pick(), 0.24 * strength));
    }
    splat(0.5, 0.5, 0, 0, colorScaled([0.92, 0.86, 0.72], 0.18 * strength));  // soft warm core
  }

  var lastTime = Date.now();
  function step(dt) {
    gl.disable(gl.BLEND);
    curlProgram.bind();
    gl.uniform2f(curlProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(curlProgram.uniforms.uVelocity, velocity.read.attach(0));
    blit(curlFBO);
    vorticityProgram.bind();
    gl.uniform2f(vorticityProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(vorticityProgram.uniforms.uVelocity, velocity.read.attach(0));
    gl.uniform1i(vorticityProgram.uniforms.uCurl, curlFBO.attach(1));
    gl.uniform1f(vorticityProgram.uniforms.curl, config.CURL);
    gl.uniform1f(vorticityProgram.uniforms.dt, dt);
    blit(velocity.write); velocity.swap();
    divergenceProgram.bind();
    gl.uniform2f(divergenceProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(divergenceProgram.uniforms.uVelocity, velocity.read.attach(0));
    blit(divergenceFBO);
    clearProgram.bind();
    gl.uniform1i(clearProgram.uniforms.uTexture, pressureFBO.read.attach(0));
    gl.uniform1f(clearProgram.uniforms.value, config.PRESSURE);
    blit(pressureFBO.write); pressureFBO.swap();
    pressureProgram.bind();
    gl.uniform2f(pressureProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(pressureProgram.uniforms.uDivergence, divergenceFBO.attach(0));
    for (var i = 0; i < config.PRESSURE_ITERATIONS; i++) {
      gl.uniform1i(pressureProgram.uniforms.uPressure, pressureFBO.read.attach(1));
      blit(pressureFBO.write); pressureFBO.swap();
    }
    gradienSubtractProgram.bind();
    gl.uniform2f(gradienSubtractProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(gradienSubtractProgram.uniforms.uPressure, pressureFBO.read.attach(0));
    gl.uniform1i(gradienSubtractProgram.uniforms.uVelocity, velocity.read.attach(1));
    blit(velocity.write); velocity.swap();
    advectionProgram.bind();
    gl.uniform2f(advectionProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform2f(advectionProgram.uniforms.dyeTexelSize, velocity.texelSizeX, velocity.texelSizeY);
    gl.uniform1i(advectionProgram.uniforms.uVelocity, velocity.read.attach(0));
    gl.uniform1i(advectionProgram.uniforms.uSource, velocity.read.attach(0));
    gl.uniform1f(advectionProgram.uniforms.dt, dt);
    gl.uniform1f(advectionProgram.uniforms.dissipation, config.VELOCITY_DISSIPATION);
    blit(velocity.write); velocity.swap();
    gl.uniform2f(advectionProgram.uniforms.dyeTexelSize, dye.texelSizeX, dye.texelSizeY);
    gl.uniform1i(advectionProgram.uniforms.uVelocity, velocity.read.attach(0));
    gl.uniform1i(advectionProgram.uniforms.uSource, dye.read.attach(1));
    gl.uniform1f(advectionProgram.uniforms.dissipation, config.DENSITY_DISSIPATION);
    blit(dye.write); dye.swap();
  }

  function render() {
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.enable(gl.BLEND);
    displayProgram.bind();
    gl.uniform1i(displayProgram.uniforms.uTexture, dye.read.attach(0));
    blit(null);
  }

  function updatePointer(p, x, y) {
    p.prevTexcoordX = p.texcoordX; p.prevTexcoordY = p.texcoordY;
    p.texcoordX = x / canvas.clientWidth; p.texcoordY = 1.0 - y / canvas.clientHeight;
    p.deltaX = p.texcoordX - p.prevTexcoordX; p.deltaY = p.texcoordY - p.prevTexcoordY;
    p.moved = Math.abs(p.deltaX) > 0 || Math.abs(p.deltaY) > 0;
  }

  var heroSection = canvas.closest ? canvas.closest('.photo-hero') : null;
  window.addEventListener('mousemove', function (e) {
    var rect = canvas.getBoundingClientRect();
    if (!introRunning) {
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) return;
    }
    var p = pointers[0];
    if (!p.movedOnce) { p.color = pick(); p.movedOnce = true; }
    updatePointer(p, e.clientX - rect.left, e.clientY - rect.top);
    if (p.moved) { splatPointer(p, introRunning ? 1.6 : 1); if (Math.random() < 0.06) p.color = pick(); }
  });
  window.addEventListener('touchmove', function (e) {
    if (introRunning) return;
    var rect = canvas.getBoundingClientRect();
    var t = e.touches[0]; if (!t) return;
    if (t.clientY < rect.top || t.clientY > rect.bottom) return;
    var p = pointers[0];
    updatePointer(p, t.clientX - rect.left, t.clientY - rect.top);
    if (p.moved) splatPointer(p, 1);
  }, { passive: true });

  var introRunning = true;
  var autoTimer = 0;
  var visible = true;   // hero in viewport
  var active = true;    // tab visible

  document.addEventListener('visibilitychange', function () { active = !document.hidden; lastTime = Date.now(); });
  if (heroSection && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting; lastTime = Date.now();
    }, { threshold: 0.02 }).observe(heroSection);
  }

  function frame() {
    requestAnimationFrame(frame);
    // Skip the solver when nothing can be seen (saves battery/GPU); keep intro alive.
    if (!introRunning && (!visible || !active)) { lastTime = Date.now(); return; }
    var now = Date.now();
    var dt = Math.min((now - lastTime) / 1000, 0.0166);
    lastTime = now;
    if (resizeCanvas()) initFramebuffers();
    // No trickle during the intro - it is a single burst that fades in.
    // Once settled, a rare, faint ambient splat keeps it quietly alive.
    if (!introRunning) {
      autoTimer += dt;
      if (autoTimer >= 7.0) { autoTimer = 0; randomSplat(0.09); }
    }
    step(dt);
    render();
  }

  initFramebuffers();
  resizeCanvas();
  initFramebuffers();
  if (splash) {
    // Home: full-screen intro bloom that fades into the hero.
    centerBurst(1);
    document.body.classList.add('fluid-intro');
    requestAnimationFrame(frame);
    var SPLASH_MS = 2200;
    setTimeout(function () {
      splash.classList.add('fade');
      document.body.classList.remove('fluid-intro');
      document.body.classList.add('fluid-behind');
      introRunning = false;
    }, SPLASH_MS);
    setTimeout(function () {
      if (splash.parentNode) splash.parentNode.removeChild(splash);
    }, SPLASH_MS + 1500);
  } else {
    // Any other page hero: no splash, just a gentle bloom into the subtle layer.
    introRunning = false;
    document.body.classList.add('fluid-behind');
    centerBurst(0.6);
    requestAnimationFrame(frame);
  }
})();
