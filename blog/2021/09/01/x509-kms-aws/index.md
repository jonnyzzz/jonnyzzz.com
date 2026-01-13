# X.509 Certificates with AWS KMS

**Date:** September 01, 2021  
**Author:** Eugene Petrenko  
**Tags:** pki-tree, x509, jvm, kotlin, AWS, certificates

---

I've done a custom [PKI](https://en.wikipedia.org/wiki/Public_key_infrastructure)
structure of [X509 certificates](https://en.wikipedia.org/wiki/X.509) 
to implement a signature service on top of it. Along
the way, I found how to generate certificates and sign data
without having private keys in my code.

Before we go, let me note, it is possible to use
[Amazon Certificate Manager](https://aws.amazon.com/certificate-manager/)
to [host private certificates](https://aws.amazon.com/certificate-manager/pricing/?nc=sn&loc=3).
By the time of writing (August 2021), every certificate would cost about $400/month, excluding
API calls. It is fine to use that for a root certificate, but it looks too much when
multiplied by `N`, as in my case. There is no API for signatures for an ACM managed
certificate too, so one would have to deal with private keys.

### Hosted Keys

Hosted (hardware or HSM) keys or certificates give a nice 
advantage — we can avoid having direct access to private keys material bytes.
Instead, we send a request to a service to generate a needed signature. 

[AWS CloudHSM](https://aws.amazon.com/cloudhsm/) or alike solutions allow ensuring
no one would ever extract a private key from our service or even AWS.
In the worst case, someone could get access to the service. 
One minimizes risks via the [IAM](https://aws.amazon.com/iam) setup and audit.

[AWS Key Management Service](https://aws.amazon.com/kms/) allows managing
RSA keys this way, having this in mind, I've started researching how to generate
certificates with keys in the KMS for my solution.

### OpenSSL

OpenSSL supports all necessary operations with X509 certificates.
The `openssl` console command could help to
decode a given certificate, validate, generate or sign. 
Ping me in the comment or on [Twitter](https://twitter.com/jonnyzzz) and I'll blog more details.
I [test the generated](https://twitter.com/jonnyzzz/status/1432325398155640834?s=20)
certificates via `openssl` command to make sure it was done correctly.

Sadly, but the `openssl` command does not support KMS or hardware keys out of the box.
One has to dig deeper into the implementation level, patches, sources, or forks. 

For my further investigation, I'd use JVM and the
[Bouncy Castle](https://www.bouncycastle.org/) library.
I'll blog more on how to do X509 certificates with the library soon,
there are many obsolete or old examples online, and it needs to
be cleared up. Let me know in the comments or 
on [Twitter](https://twitter.com/jonnyzzz), so it would happen earlier.

### Bouncy Castle on JVM

One usually generates a child X509 certificate using the `JcaX509v3CertificateBuilder`
from [Bouncy Castle](https://www.bouncycastle.org/).
It takes the parent certificate and signs a child certificate with the
parent one. 

Here is a simplified example to generate a signed subordinate certificate:

```kotlin
val parentCa: X509CertificateHolder = TODO("Load parent certificate")
val builder = JcaX509v3CertificateBuilder(
  parentCa.subject,
  BigInteger("C0 Ff Ee"),
  Date(),
  parentCa.notAfter,
  rootSubject,
  childCaPublicKey,
)
//TODO: condifigure the builder to add extensions and params
val signer: ContentSigner = TODO("Implement the Content Signer")
val childCert: X509CertificateHolder = builder.build(signer)
//This is the child certificate, use JcaPEMWriter for PEM encoding 
return childCert
```

As we see, it does not require a private key to run. It uses only
the RSA public key of the child certificate. No secretes so far.

The `ContentSigner` interface encapsulates the signature need.
Usually, we use `JcaContentSignerBuilder` to create an instance 
from a private key of the parent certificate. It is not the case here. 

### ContentSigner implementation via KMS

We implement the `ContentSigner` directly, and do a remote
call to the AWS service for the signature. We do not have
access to the actual private key bytes. I use the following 
implementation for that:

```kotlin
private class AwsKmsContentSignerSha512WithRSA(
  private val aws: KmsClient,
  private val keyId: String,
) : ContentSigner {
  private val bytesToSign = MessageDigest.getInstance("SHA-512")
  private val wrapper = DigestOutputStream(OutputStream.nullOutputStream(), bytesToSign)
  override fun getOutputStream() = wrapper
  override fun getAlgorithmIdentifier() = AlgorithmIdentifier(PKCSObjectIdentifiers.sha512WithRSAEncryption)
  override fun getSignature(): ByteArray {
    return aws.sign { req ->
      req.keyId(keyId)
      req.message(SdkBytes.fromByteArray(bytesToSign.digest()))
      req.messageType(MessageType.DIGEST)
      req.signingAlgorithm(SigningAlgorithmSpec.RSASSA_PKCS1_V1_5_SHA_512)
    }.signature().asByteArray()
  }
}
```

As we see, the code computes SHA-512 digest from the actual data,
that needs to be signed. No matter how big is the certificate, it
will only send a short message to the AWS.

This code uses the [AWS KMS client](https://aws.amazon.com/sdk-for-java/) and a `keyId`. 
It sends a request to AWS to generate the signature, it does not use the actual private
key directly in our code. That is enough for the BouncyCastle library
to sign the new certificate or data for us.

You may also note, that there are many tricky bound constants in the code snippet:
 - `SHA-512`
 - `PKCSObjectIdentifiers.sha512WithRSAEncryption`
 - `SigningAlgorithmSpec.RSASSA_PKCS1_V1_5_SHA_512`

Similarly, it could be tuned to use the SHA-256 signature instead. Note, it would require changing
all three parameters. 

The `ContentSigner` interface is widely used in the BouncyCastle library, 
so we could use it at many other places to implement signatures that we
need, for example, a CMS (S/MIME) one.

## Conclusion

It appeared easy to use BouncyCastle library to implement 
cryptography on top of the AWS KMS. It opens the way for writing
safe applications which deal with X509 certificates without direct
access to private keys.