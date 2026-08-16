# Transform Composition and Ground Truth

The generator intentionally keeps the transform pipeline explicit.

## Reference-side transform

A local high-resolution reference view is first rendered from the same physical wafer scene as the search image.

The acquisition transform is

`A = s R(theta)`

about the reference center.

OpenCV implements this as a rotation matrix with a scale factor around `(499.5,499.5)` using Lanczos interpolation.

## Forward mapping

A reference pixel `p_r` maps to search coordinates by

`p_s = c_s + A^{-1}(p_r-c_r)/10`.

The division by 10 converts 1 nm/px reference coordinates into 10 nm/px search coordinates.

## Inverse mapping

For any search coordinate `p_s`,

`p_r = A [10(p_s-c_s)] + c_r`.

Because `s > 0`, the matrix is nonsingular. The implementation computes the inverse numerically from the 2×2 rotation/scale matrix and preserves double precision until annotation output.

## Why composition order matters

Rotation and scale are applied around the reference center, not the global origin. The center-preserving composition is:

`T(c_r) R(theta) S(s) T(-c_r)`.

Applying `R*S` around the image origin would move the pattern center and invalidate the derived location.

## Annotation

The four reference corners are transformed through the exact affine mapping. The center is independently mapped through the same matrix. These are continuous-valued floating-point coordinates; display/output rounding is delayed until presentation only.

## Numerical safeguards

- scale must be strictly positive;
- finite numeric values are required;
- inverse is only computed for nonsingular positive-scale transforms;
- predicted centers must fall inside the search image;
- extreme or physically implausible feature-derived scale ratios are rejected or heavily penalized.
