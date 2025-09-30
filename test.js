console.log(require.resolve.paths('recast'));
try {
    require('recast');
    console.log('recast found');
} catch (e) {
    console.error(e.message);
}