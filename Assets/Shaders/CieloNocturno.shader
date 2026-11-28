// Cielo de la Nochebuena: degradado + estrellas que titilan + luna + aurora boreal animada.
// Es un shader de "Skybox": se dibuja detrás de todo. Todo se calcula con la DIRECCIÓN
// en la que mira cada píxel (no usa texturas).
Shader "Navidad/CieloNocturno"
{
    Properties
    {
        _ColorArriba ("Color arriba", Color) = (0.01, 0.015, 0.05, 1)
        _ColorHorizonte ("Color horizonte", Color) = (0.07, 0.1, 0.22, 1)
        _ColorAbajo ("Color abajo", Color) = (0.02, 0.025, 0.05, 1)
        _DensidadEstrellas ("Densidad estrellas", Range(0.97, 0.999)) = 0.988
        _BrilloEstrellas ("Brillo estrellas", Float) = 2.5
        _DirLuna ("Dirección luna", Vector) = (-0.45, 0.55, -0.7, 0)
        _ColorLuna ("Color luna", Color) = (0.9, 0.95, 1, 1)
        _AuroraA ("Aurora color bajo", Color) = (0.1, 1.0, 0.45, 1)
        _AuroraB ("Aurora color medio", Color) = (0.5, 0.2, 1.0, 1)
        _AuroraC ("Aurora color punta", Color) = (1.0, 0.3, 0.6, 1)
        _AuroraIntensidad ("Aurora intensidad", Float) = 1.6
        _AuroraVelocidad ("Aurora velocidad", Float) = 1.0
        _Niebla ("Niebla de ventisca (0-1)", Range(0, 1)) = 0
        _ColorNiebla ("Color de la niebla", Color) = (0.32, 0.38, 0.48, 1)
    }
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" }
        Cull Off ZWrite Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 _ColorArriba, _ColorHorizonte, _ColorAbajo, _ColorLuna, _AuroraA, _AuroraB, _AuroraC, _DirLuna;
            float _DensidadEstrellas, _BrilloEstrellas, _AuroraIntensidad, _AuroraVelocidad, _Niebla;
            float4 _ColorNiebla;

            struct appdata { float4 vertex : POSITION; };
            struct v2f { float4 pos : SV_POSITION; float3 dir : TEXCOORD0; };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.dir = v.vertex.xyz;      // en un skybox, la posición del vértice = dirección
                return o;
            }

            // número "aleatorio" a partir de una celda (siempre da lo mismo para la misma celda)
            float hash13(float3 p)
            {
                p = frac(p * 0.1031);
                p += dot(p, p.zyx + 31.32);
                return frac((p.x + p.y) * p.z);
            }

            float3 estrellas(float3 d, float t)
            {
                float3 total = 0;
                // dos capas: estrellas grandes y pequeñas
                for (int capa = 0; capa < 2; capa++)
                {
                    float escala = capa == 0 ? 90.0 : 180.0;
                    float3 p = d * escala;
                    float3 celda = floor(p);
                    float h = hash13(celda + capa * 17.0);
                    if (h > _DensidadEstrellas)
                    {
                        float3 centro = celda + 0.5 + (float3(hash13(celda + 1.3), hash13(celda + 2.7), hash13(celda + 5.1)) - 0.5) * 0.6;
                        float dist = length(p - centro);
                        float brillo = smoothstep(0.35, 0.0, dist);
                        float titileo = 0.6 + 0.4 * sin(t * (1.5 + h * 4.0) + h * 80.0);
                        float3 tinte = lerp(float3(0.8, 0.85, 1.0), float3(1.0, 0.9, 0.75), frac(h * 13.0));
                        total += tinte * brillo * titileo * (capa == 0 ? 1.0 : 0.6);
                    }
                }
                return total * _BrilloEstrellas;
            }

            // Patrón de las "cortinas" en el plano del techo: 2 cortinas onduladas, cada una con rayitos verticales.
            float cortinas(float2 q, float t)
            {
                float f = 0;
                [unroll] for (int k = 0; k < 2; k++)
                {
                    float w = q.x * (1.3 + 0.5 * k) + t * (0.06 + 0.03 * k) + k * 2.1;
                    float curva = sin(w) * 0.22 + sin(w * 2.7 + 1.3 + t * 0.05) * 0.07 + 1.05 + k * 0.32;
                    float dist = abs(q.y - curva);
                    float banda = smoothstep(0.07, 0.0, dist);
                    // rayos finos que "corren" a lo largo de la cortina
                    float rayos = pow(saturate(0.5 + 0.5 * sin(q.x * (40.0 + 13.0 * k) + sin(q.x * 5.0 + t * 0.35) * 3.0 + t * 0.6)), 1.5)
                                * (0.45 + 0.55 * saturate(0.5 + 0.5 * sin(q.x * 6.3 + t * 0.21 + k * 2.0) * sin(q.x * 2.1 - t * 0.13)));
                    rayos = 0.25 + 0.75 * rayos;
                    f += banda * rayos * (1.0 - 0.3 * k);
                }
                return f;
            }

            // AURORA por CAPAS: se dibuja el mismo patrón a 36 "alturas". Las capas altas se ven más arriba en el
            // cielo, así cada cortina tiene una orilla de abajo brillante (verde) y sube desvaneciéndose (violeta / rosa).
            float3 aurora(float3 d, float t)
            {
                if (d.y < 0.01) return 0;
                float2 baseUV = d.xz / (d.y * 1.6 + 0.25);
                float3 acc = 0;
                const int CAPAS = 36;
                float jit = hash13(d * 937.0);          // tramado: cada píxel desplaza un poco las capas => no se ven rayas
                [loop] for (int i = 0; i < CAPAS; i++)
                {
                    float fi = i;
                    float2 q = baseUV * (1.0 + (fi + jit) * 0.027);
                    float f = cortinas(q, t);
                    float h = fi / (CAPAS - 1);
                    float3 c = lerp(_AuroraA.rgb, _AuroraB.rgb, smoothstep(0.1, 0.65, h));
                    c = lerp(c, _AuroraC.rgb, smoothstep(0.6, 1.0, h));
                    acc += c * f * exp2(-fi * 0.06);
                }
                float fade = smoothstep(0.01, 0.16, d.y) * (1.0 - smoothstep(0.6, 0.95, d.y));
                return acc * fade * _AuroraIntensidad * 0.085;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float3 d = normalize(i.dir);
                float t = _Time.y * _AuroraVelocidad;

                // 1) degradado del cielo
                float3 col = d.y > 0
                    ? lerp(_ColorHorizonte.rgb, _ColorArriba.rgb, pow(saturate(d.y), 0.45))
                    : lerp(_ColorHorizonte.rgb, _ColorAbajo.rgb, saturate(-d.y * 4.0));

                // 2) estrellas (solo arriba del horizonte)
                col += estrellas(d, _Time.y) * smoothstep(0.0, 0.15, d.y);

                // 3) luna con halo
                float3 ld = normalize(_DirLuna.xyz);
                float c = dot(d, ld);
                col += _ColorLuna.rgb * (smoothstep(0.9993, 0.9996, c) * 3.0 + pow(saturate(c), 600.0) * 0.6 + pow(saturate(c), 40.0) * 0.08);

                // 4) aurora boreal
                float3 au = aurora(d, t);
                col += au;
                col += _AuroraA.rgb * 0.012 * smoothstep(0.0, 0.3, d.y) * (1 - smoothstep(0.3, 0.8, d.y));   // resplandor suave del cielo

                // 5) ventisca: el cielo también se tapa de nieve (si no, quedaba una mancha negra arriba de los
                //    techos mientras todo lo demás se ponía gris). Más tapado cerca del horizonte.
                float tapado = _Niebla * lerp(1.0, 0.82, smoothstep(0.0, 0.7, d.y));
                col = lerp(col, _ColorNiebla.rgb, saturate(tapado));

                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    Fallback Off
}
