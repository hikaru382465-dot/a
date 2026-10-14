// 絵の形はそのままで、中を単色（白）にぬる。当たった瞬間の「しろ光り」に使う
// 使い方：このシェーダーでマテリアルを作り、HitFlash の flashMaterial に入れる
Shader "DotMeikyu/SpriteFlash"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _FlashColor ("Flash Color", Color) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial) float4 _FlashColor; CBUFFER_END
            struct A { float4 pos : POSITION; float2 uv : TEXCOORD0; float4 col : COLOR; };
            struct V { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; float4 col : COLOR; };
            V vert(A a) { V v; v.pos = TransformObjectToHClip(a.pos.xyz); v.uv = a.uv; v.col = a.col; return v; }
            half4 frag(V v) : SV_Target { half a = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, v.uv).a * v.col.a; return half4(_FlashColor.rgb, a * _FlashColor.a); }
            ENDHLSL
        }
    }
}
